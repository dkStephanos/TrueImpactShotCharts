# The code in this file was lifted and modified. The original source author/repo: https://github.com/linouk23/NBA-Player-Movements
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import Tuple
from matplotlib import animation
from matplotlib.patches import Circle, Polygon as MplPolygon
from matplotlib.colors import LinearSegmentedColormap
from shapely.geometry import Polygon
from IPython.display import HTML
from scipy.spatial import Voronoi, voronoi_plot_2d
from sklearn.metrics import roc_curve, auc
from scipy.interpolate import griddata
from code.io.TrackingProcessor import TrackingProcessor
from code.util.FeatureUtil import ShotRegionUtil


class VisUtil:
    INTERVAL: int = 2
    COURT_DIMS: Tuple[int, int, int, int] = (
        -47,
        47,
        -25,
        25,
    )  # Court dimensions: X_MIN, X_MAX, Y_MIN, Y_MAX
    COL_WIDTH: float = 0.3
    SCALE: float = 1.65
    FONTSIZE: int = 6
    NORMALIZATION_COEF: float = (
        7  # Define the normalization coefficient for the ball radius
    )
    PLAYER_CIRCLE_SIZE: float = 12 / NORMALIZATION_COEF
    DIFF: int = 6
    X_CENTER: float = 0.0
    Y_CENTER: float = 0.0

    TEAM_COLOR_DICT = {
        "1610612737": ("#E13A3E", "Atlanta Hawks"),
        "1610612738": ("#008348", "Boston Celtics"),
        "1610612751": ("#061922", "Brooklyn Nets"),
        "1610612766": ("#1D1160", "Charlotte Hornets"),
        "1610612741": ("#CE1141", "Chicago Bulls"),
        "1610612739": ("#860038", "Cleveland Cavaliers"),
        "1610612742": ("#007DC5", "Dallas Mavericks"),
        "1610612743": ("#4D90CD", "Denver Nuggets"),
        "1610612765": ("#006BB6", "Detroit Pistons"),
        "1610612744": ("#FDB927", "Golden State Warriors"),
        "1610612745": ("#CE1141", "Houston Rockets"),
        "1610612754": ("#00275D", "Indiana Pacers"),
        "1610612746": ("#ED174C", "Los Angeles Clippers"),
        "1610612747": ("#552582", "Los Angeles Lakers"),
        "1610612763": ("#0F586C", "Memphis Grizzlies"),
        "1610612748": ("#98002E", "Miami Heat"),
        "1610612749": ("#00471B", "Milwaukee Bucks"),
        "1610612750": ("#005083", "Minnesota Timberwolves"),
        "1610612740": ("#002B5C", "New Orleans Pelicans"),
        "1610612752": ("#006BB6", "New York Knicks"),
        "1610612760": ("#007DC3", "Oklahoma City Thunder"),
        "1610612753": ("#007DC5", "Orlando Magic"),
        "1610612755": ("#006BB6", "Philadelphia 76ers"),
        "1610612756": ("#1D1160", "Phoenix Suns"),
        "1610612757": ("#E03A3E", "Portland Trail Blazers"),
        "1610612758": ("#724C9F", "Sacramento Kings"),
        "1610612759": ("#BAC3C9", "San Antonio Spurs"),
        "1610612761": ("#CE1141", "Toronto Raptors"),
        "1610612762": ("#00471B", "Utah Jazz"),
        "1610612764": ("#002B5C", "Washington Wizards"),
    }

    # NOTE: This class is designed to work with a single game's worth of data
    # TODO: allow for more dynamic seeting of home/away team info
    def __init__(self, tracking_df: pd.DataFrame):
        plt.ioff()
        self.tracking_df: pd.DataFrame = tracking_df
        team_ids = tracking_df["teamId"].head(25).dropna().unique()
        self.home_team_id = team_ids[0]
        self.away_team_id = team_ids[1]
        self.home_team_tuple = (
            self.TEAM_COLOR_DICT[team_ids[0]][1],
            self.TEAM_COLOR_DICT[team_ids[0]][0],
        )
        self.away_team_tuple = (
            self.TEAM_COLOR_DICT[team_ids[1]][1],
            self.TEAM_COLOR_DICT[team_ids[1]][0],
        )

        players_df = pd.read_csv(
            "data/src/basic_player_info.csv",
            dtype={"person_id": str, "jersey_num": str},
        )
        self.players_dict = {
            row["person_id"]: (
                f"{row['nickname'][0]}. {row['last_name']}",
                row["jersey_num"],
            )
            for index, row in players_df.iterrows()
        }

        self.fig, self.ax = None, None
        self.last_animation = (
            {}
        )  # To store the reference to the last animation, outer dict key is interval, inner is event_num
        self.court = VisUtil.load_court_image()

    @staticmethod
    def load_court_image():
        return plt.imread("data/img/app/fullcourt.png")

    def setup_visualization(self, moments_df):
        VisUtil.setup_court(self.ax)
        home_players_ids, away_players_ids = self.extract_moment_players(moments_df)
        self.setup_players_and_ball(home_players_ids, away_players_ids)

        return self.setup_labels(home_players_ids, away_players_ids)

    def extract_moment_players(self, moments_df):
        # Collect home and away player_ids (ball has a teamId of -1)
        players_df = moments_df.loc[
            moments_df["teamId"] != "-1", ["playerId", "playerName", "teamId"]
        ].drop_duplicates()

        home_players_ids = list(
            players_df.loc[players_df["teamId"] == self.home_team_id][
                "playerId"
            ].unique()
        )
        away_players_ids = list(
            players_df.loc[players_df["teamId"] == self.away_team_id][
                "playerId"
            ].unique()
        )

        return home_players_ids, away_players_ids

    @classmethod
    def setup_court(cls, ax):
        x_min, x_max, y_min, y_max = cls.COURT_DIMS
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.axis("off")

        # Display the court image
        ax.imshow(
            VisUtil.load_court_image(), zorder=0, extent=[x_min, x_max, y_min, y_max]
        )
        ax.set_aspect("equal", "box")

    @classmethod
    def set_halfcourt(cls, ax, basket_x=41.75):
        if basket_x > 0:
            ax.set_xlim(0, 47)
        else:
            ax.set_xlim(-47, 0)

    def setup_players_and_ball(self, home_players_ids, away_players_ids):
        # Set up and add circles for the players and ball
        self.player_circles = {
            player_id: Circle(
                (0, 0),  # Initial position; this should be updated dynamically
                self.PLAYER_CIRCLE_SIZE,
                color=self.TEAM_COLOR_DICT[
                    (
                        self.home_team_id
                        if player_id in home_players_ids
                        else self.away_team_id
                    )
                ][
                    0
                ],  # Team color based on player's team
            )
            for player_id in home_players_ids + away_players_ids
        }

        self.ball_circle = Circle(
            (0, 0),  # Initial ball position
            self.PLAYER_CIRCLE_SIZE,
            color="#E2561A",  # Hardcoded orange for the ball
        )

        # Add all player circles and the ball circle to the axes
        for circle in self.player_circles.values():
            self.ax.add_patch(circle)
        self.ax.add_patch(self.ball_circle)

    def setup_labels(self, home_players_ids, away_players_ids):
        # Prepare table
        column_labels = tuple([self.home_team_tuple[0], self.away_team_tuple[0]])
        column_colours = tuple(
            [
                self.home_team_tuple[1],
                self.away_team_tuple[1],
            ]
        )
        cell_colours = [column_colours for _ in range(5)]

        # Create player cell entries
        home_players = [
            " #".join(
                [self.players_dict[player_id][0], str(self.players_dict[player_id][1])]
            )
            for player_id in home_players_ids
        ]
        away_players = [
            " #".join(
                [self.players_dict[player_id][0], str(self.players_dict[player_id][1])]
            )
            for player_id in away_players_ids
        ]

        # Render and scale the table
        table = plt.table(
            cellText=list(zip(home_players, away_players)),
            colLabels=column_labels,
            colColours=column_colours,
            colWidths=[self.COL_WIDTH, self.COL_WIDTH],
            loc="bottom",
            cellColours=cell_colours,
            fontsize=self.FONTSIZE,
            cellLoc="center",
        )
        table.scale(1, self.SCALE)

        # Set up clock info an annotations
        clock_info = self.ax.annotate(
            "",
            xy=[self.X_CENTER, 24],
            color="black",
            horizontalalignment="center",
            verticalalignment="center",
        )

        # Set up annotations for players dynamically based on current player positions in the frame
        annotations = {
            player_id: self.ax.annotate(
                f"{self.players_dict[player_id][1]}",  # jersey_num
                xy=(
                    0,
                    0,
                ),  # Initial position; this should be updated dynamically in the animation loop
                color="w",
                horizontalalignment="center",
                verticalalignment="center",
                fontweight="bold",
            )
            for player_id in home_players_ids + away_players_ids
        }

        return annotations, clock_info

    def precompute_frames(moments_df):
        # First, add a frame_id to group on
        moments_df = moments_df.copy()
        moments_df.loc[:, "frame_id"] = moments_df["wcTime"].factorize()[0]

        # Include ball data and player data without filtering out the ball prematurely
        player_frames = moments_df.drop(
            columns=["gameId", "teamAbbr", "gameDate"]
        )  # Keep ball data

        # Precompute player data for each frame, ensure to separate ball data here
        player_data_by_frame = (
            player_frames[player_frames["teamId"] != "-1"]
            .groupby("frame_id")
            .apply(lambda df: df[["playerId", "x", "y", "z"]].to_dict(orient="records"))
        )

        # Separately handle ball data to ensure it's correctly processed
        ball_data_by_frame = (
            player_frames[player_frames["teamId"] == "-1"]
            .groupby("frame_id")
            .apply(lambda df: df[["x", "y", "z"]].iloc[0].to_dict())
        )

        # Now create the precomputed_data list
        return [
            {
                "quarter": frame["period"].iloc[
                    0
                ],  # Assuming period is the same for all rows in the same frame
                "game_clock": frame["gcTime"].iloc[0],
                "shot_clock": frame["scTime"].iloc[0],
                "ball": {
                    "x": ball_data_by_frame.loc[idx]["x"],
                    "y": ball_data_by_frame.loc[idx]["y"],
                    "z": ball_data_by_frame.loc[idx]["z"],
                },
                "players": player_data_by_frame.loc[idx],
            }
            for idx, frame in player_frames.groupby("frame_id")
        ]

    def animate(self, frame: int, precomputed_data, annotations, clock_info):
        moment = precomputed_data[frame]

        # Update the game and shot clock display
        clock_info.set_text(
            f"Quarter {moment['quarter']}\n{int(moment['game_clock']) // 60:02d}:{int(moment['game_clock']) % 60:02d}\n{moment['shot_clock']:.1f}"
        )

        # Update player positions and annotations using player IDs as dictionary keys
        updated_artists = [self.ball_circle, clock_info]

        for player in moment["players"]:
            player_id = player[
                "playerId"
            ]  # Assuming each player dictionary has an 'id' key
            if player_id in annotations:
                self.player_circles[player_id].center = (player["x"], player["y"])
                annotations[player_id].set_position((player["x"], player["y"]))
                updated_artists.extend(
                    [self.player_circles[player_id], annotations[player_id]]
                )

        # Update the ball's position and radius
        self.ball_circle.center = (moment["ball"]["x"], moment["ball"]["y"])
        self.ball_circle.radius = moment["ball"]["z"] / self.NORMALIZATION_COEF

        return updated_artists

    def _create_animation(self, possession, interval: int):
        """Support method for display/save methods with caching support."""
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        moments_df = TrackingProcessor.extract_possession_moments(
            self.tracking_df, possession
        )
        annotations, clock_info = self.setup_visualization(moments_df)
        precomputed_data = VisUtil.precompute_frames(moments_df)

        return animation.FuncAnimation(
            self.fig,
            self.animate,
            fargs=(precomputed_data, annotations, clock_info),
            frames=len(precomputed_data),
            interval=interval,
            blit=True,
        )

    def display_animation(self, possession):
        """Configure and display the animation for the specified possession number. Designed for inline Jupyter cells"""
        anim = self._create_animation(possession=possession, interval=40)
        return HTML(anim.to_html5_video())

    def save_animation(self, possession, filename="animation.mp4"):
        """Save the animation for the specified possession number to a file."""
        anim = self._create_animation(
            possession=possession, interval=40
        )  # Create the animation

        # Check the filename extension to decide on writer
        if filename.endswith(".gif"):
            writer = animation.PillowWriter(fps=25)
        else:
            # This requires having ffmpeg installed
            writer = "ffmpeg"  # Default writer for MP4 and AVI

        # Save the animation
        anim.save(
            filename, writer=writer, dpi=80
        )  # You can adjust the DPI based on your resolution needs

    def plot_frame_at_timestamp(self, timestamp):
        """Plot a single frame based on the given timestamp."""
        self.fig, self.ax = plt.subplots(figsize=(12, 8))

        # Filter the dataframe for the specific timestamp
        moments_df = self.tracking_df[self.tracking_df["wcTime"] == timestamp]

        if moments_df.empty:
            raise ValueError("No data available for the specified timestamp")

        # Setup the court and game elements
        annotations, clock_info = self.setup_visualization(moments_df)

        # Since we only need one frame, we can directly take the necessary data
        moment = moments_df.iloc[0]
        game_clock = moment["gcTime"]
        shot_clock = moment["scTime"]
        quarter = moment["period"]

        # Update the annotations and player positions
        for index, row in moments_df.iterrows():
            player_id = row["playerId"]
            if player_id in self.player_circles:
                self.player_circles[player_id].center = (row["x"], row["y"])
                annotations[player_id].set_position((row["x"], row["y"]))

        # Update the ball's position
        ball_data = moments_df[moments_df["teamId"] == "-1"].iloc[0]
        self.ball_circle.center = (ball_data["x"], ball_data["y"])
        self.ball_circle.radius = ball_data["z"] / self.NORMALIZATION_COEF

        # Update the clock info
        clock_info.set_text(
            f"Quarter {quarter}\n{int(game_clock) // 60:02d}:{int(game_clock) % 60:02d}\n{shot_clock:.1f}"
        )

        # Redraw the frame with the updated positions and information
        self.ax.figure.canvas.draw()
        plt.show()

    def plot_voronoi_at_timestamp(self, timestamp, basket_x, return_data=False):
        """Plot or return the Voronoi diagram for the players' positions at a specific timestamp with team-based cell shading,
        confined to the half of the court based on basket location."""
        moments_df = self.tracking_df[self.tracking_df["wcTime"] == timestamp]

        if moments_df.empty:
            raise ValueError("No data available for the specified timestamp")

        if not return_data:
            self.fig, self.ax = plt.subplots(figsize=(12, 8))
            self.setup_visualization(
                moments_df
            )  # Setup the court visualization based on the current moments dataframe

        ball_data = (
            moments_df[moments_df["teamId"] == "-1"].iloc[0]
            if not moments_df[moments_df["teamId"] == "-1"].empty
            else None
        )
        player_data = moments_df[moments_df["teamId"] != "-1"][
            ["playerId", "x", "y", "teamId"]
        ].values

        # Define artificial boundary points at the edges of the court
        boundary_points = np.array([[-47, -25], [-47, 25], [47, -25], [47, 25]])
        all_points = np.vstack([player_data[:, 1:3], boundary_points])

        vor = Voronoi(all_points)

        # Determine half-court boundaries based on the basket location
        if basket_x > 0:
            half_court_bounds = Polygon([(0, -25), (0, 25), (47, 25), (47, -25)])
        else:
            half_court_bounds = Polygon([(-47, -25), (-47, 25), (0, 25), (0, -25)])

        if not return_data:
            voronoi_plot_2d(
                vor,
                ax=self.ax,
                show_vertices=False,
                show_points=False,
                line_colors="orange",
                line_width=2,
                line_alpha=0.6,
            )

        player_regions = {}
        for point_index, region_index in enumerate(vor.point_region):
            region = vor.regions[region_index]
            if all(v >= 0 for v in region) and region:  # Ensure the region is bounded
                vertices = vor.vertices[region]
                if vertices.size > 0:
                    polygon = Polygon(vertices)
                    clipped_polygon = polygon.intersection(
                        half_court_bounds
                    )  # Clip to court bounds
                    if not clipped_polygon.is_empty:
                        if point_index < len(
                            player_data
                        ):  # Check if index is within the range of player_data
                            player_id = str(player_data[point_index][0])
                            team_id = str(player_data[point_index][3])
                            if return_data:
                                player_regions[player_id] = clipped_polygon
                            else:
                                team_color = self.TEAM_COLOR_DICT.get(
                                    team_id, "#808080"
                                )[0]
                                patch = MplPolygon(
                                    list(clipped_polygon.exterior.coords),
                                    color=team_color,
                                    alpha=0.3,
                                )
                                self.ax.add_patch(patch)
                        else:
                            continue  # Skip boundary points which do not correspond to any player

        if return_data:
            return player_regions
        else:
            # Set plot limits to the appropriate half-court dimensions
            self.ax.set_xlim([0, 47] if basket_x > 0 else [-47, 0])
            self.ax.set_ylim(-25, 25)

            # Plot players
            for index, row in moments_df.iterrows():
                player_id = row["playerId"]
                if player_id in self.player_circles:
                    circle = self.player_circles[player_id]
                    circle.center = (row["x"], row["y"])
                    self.ax.add_patch(circle)
                    self.ax.annotate(
                        f"{self.players_dict[player_id][1]}",
                        xy=(row["x"], row["y"]),
                        color="white",
                        ha="center",
                        va="center",
                        fontweight="bold",
                        fontsize=10,
                    )

            # Plot the ball if data is available
            if ball_data is not None:
                ball_circle = Circle(
                    (ball_data["x"], ball_data["y"]),
                    ball_data["z"] / self.NORMALIZATION_COEF,
                    color="orange",
                    zorder=5,
                )
                self.ax.add_patch(ball_circle)

            self.ax.figure.canvas.draw()

            self.ax.axis("off")
            plt.show()

    def plot_court_hexmap(
        df, x_col, y_col, label="Density (log scale)", return_data=False
    ):
        """
        Plots a hexmap of locations on the basketball court based on provided x and y coordinates.
        Each cell represents approximately 1.5 feet in radius, and cells are color-weighted based on the density.
        This version adjusts the plot to display only half-court and changes the color scale for better visibility.

        Args:
            df (DataFrame): The DataFrame containing the data to plot.
            x_col (str): The name of the column in df that contains the x coordinates.
            y_col (str): The name of the column in df that contains the y coordinates.
            label (str): Chart label to be applied.
        """
        # Create a new figure and axes
        fig, ax = plt.subplots(figsize=(12, 8))

        # Draw the court
        VisUtil.setup_court(ax)

        # Mirror data points across half court for plotting
        df = TrackingProcessor.mirror_court_data(df, x_col, y_col)

        # Plotting the data using hexbin
        hexbin = ax.hexbin(
            df[x_col],
            df[y_col],
            gridsize=int(
                (47 / 1.5) / 2
            ),  # based on court dimensions and desired hex radius
            cmap="viridis",  # Changed to a more visually distinct colormap
            bins="log",  # Logarithmic scale to enhance visibility for sparse data
            edgecolors="black",
            linewidth=0.5,
            extent=[
                0,
                47,
                -25,
                25,
            ],  # Set the extent to match the half-court dimensions
        )

        # Set plot limits to only show half-court
        VisUtil.set_halfcourt(ax)

        if return_data:
            # Create DataFrame from hexbin data
            hexbin_data = {
                "centers": hexbin.get_offsets(),
                "densities": hexbin.get_array(),
            }
            hexbin_df = pd.DataFrame(hexbin_data["centers"], columns=["x", "y"])
            hexbin_df["density"] = hexbin_data["densities"]
            plt.close(fig)  # Close the plot to prevent it from showing
            return hexbin_df
        else:
            # Add a color bar
            cbar = plt.colorbar(hexbin, ax=ax, pad=0.01)
            cbar.set_label(label)

            # Retrieve counts from hexbin and determine tick labels directly from the bin counts
            counts = hexbin.get_array()
            unique_counts = np.unique(counts[counts > 0]).astype(
                int
            )  # Get unique non-zero counts as integers

            # Sort unique counts to ensure they are in increasing order for setting ticks
            sorted_counts = np.sort(unique_counts)

            # Generate indices to pick exactly 8 labels, if there are enough unique counts
            num_labels = min(
                8, len(sorted_counts)
            )  # Use 8 or fewer if there aren't enough unique counts
            indices = np.linspace(0, len(sorted_counts) - 1, num=num_labels, dtype=int)
            selected_ticks = sorted_counts[indices]

            # Apply these selected counts as ticks to the color bar
            cbar.set_ticks(selected_ticks)  # Set ticks at selected counts
            cbar.set_ticklabels(selected_ticks)  # Use the selected counts as labels

            # Disable minor ticks on the colorbar to avoid extra ticks
            cbar.ax.minorticks_off()

            # Set plot limits and disable axis
            ax.axis("off")

            # Display the plot
            plt.show()

    def plot_topographical_heatmap(
        shots_df,
        x_col="shot_x",
        y_col="shot_y",
        weight_col="true_impact_points_produced",
        grid_density=100,
        ax=None,
    ):
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 11))

        # Filter and clean data
        valid_shots = shots_df[shots_df['shot_classification'] != 'beyond_halfcourt'].copy()
        valid_shots = valid_shots.dropna(subset=[x_col, y_col, weight_col])
        mean_value = valid_shots[weight_col].mean()
        
        print(f"Statistics for {weight_col}:")
        print(valid_shots[weight_col].describe())
        
        # Add boundary points with higher density near edges
        boundary_points = []
        
        # Create denser boundary points
        x_bounds = np.linspace(-2, 47, 50)
        y_bounds = np.linspace(-25, 25, 50)
        
        # Add zero points along boundaries
        for x in x_bounds:
            boundary_points.append([x, -25, 0])
            boundary_points.append([x, 25, 0])
        for y in y_bounds:
            boundary_points.append([47, y, 0])
            boundary_points.append([0, y, 0])
        
        # Add backcourt zeros
        for x in np.linspace(-2, 0, 10):
            for y in np.linspace(-25, 25, 10):
                boundary_points.append([x, y, 0])

        # Add background mean value points with higher density
        for x in np.linspace(0, 47, 30):
            for y in np.linspace(-24.9, 24.9, 30):
                # Use different base values for different regions
                if x > 39:  # Near basket
                    base_value = mean_value * 0.9
                elif x < 23.25:  # 3pt line and beyond
                    base_value = mean_value * 0.7
                else:  # Mid-range
                    base_value = mean_value * 0.8
                boundary_points.append([x, y, base_value])

        boundary_df = pd.DataFrame(boundary_points, columns=[x_col, y_col, weight_col])
        valid_shots = pd.concat([valid_shots, boundary_df])

        # Generate grid
        xi = np.linspace(-2, 47, grid_density)
        yi = np.linspace(-25, 25, grid_density)
        xi, yi = np.meshgrid(xi, yi)


        zi = griddata(
            (valid_shots[x_col], valid_shots[y_col]), 
            valid_shots[weight_col],
            (xi, yi),
            method='linear',
            fill_value=mean_value
        )

        # Create court mask
        court_mask = (xi <= 47) & (yi >= -25) & (yi <= 25)
        zi[~court_mask] = 0

        # Apply minimal smoothing
        from scipy.ndimage import gaussian_filter
        zi = gaussian_filter(zi, sigma=0.8)

        max_val = 2.0
        levels = np.linspace(0, max_val, 20)

        # Plot filled contours
        c = ax.contourf(
            xi, yi, zi,
            levels=levels,
            cmap='RdYlBu_r',
            alpha=0.8,
            extend='both',
            vmin=0,
            vmax=max_val
        )
        plt.colorbar(c, ax=ax, label=f'{weight_col} (points per shot)')

        # Add contour lines with reduced frequency
        contour = ax.contour(
            xi, yi, zi,
            levels=levels[::3],
            colors='black',
            linewidths=0.3,
            alpha=0.2
        )

        # Draw the court
        VisUtil.setup_court(ax)

        # Set court limits
        ax.set_xlim(-2, 47)
        ax.set_ylim(-25, 25)

        plt.title(f"Shot Value Topography: {weight_col}")
        plt.show()

        return zi
    
    @staticmethod
    def plot_shots_and_regions(shots_df, x_col="shot_x", y_col="shot_y", ax=None):
        """
        Plot shot attempts and overlay shot regions on a half-court diagram.

        Args:
            shots_df (DataFrame): DataFrame containing shot coordinates and optionally shot outcomes.
            x_col (str): The name of the column in shots_df that contains the x coordinates.
            y_col (str): The name of the column in shots_df that contains the y coordinates.
            ax (matplotlib.axes._subplots.AxesSubplot, optional): Matplotlib subplot object to plot on.
                                                                If None, creates a new figure and axis.
        """
        if ax is None:
            fig, ax = plt.subplots(figsize=(12, 11))
            VisUtil.setup_court(ax)

        shots_df = TrackingProcessor.mirror_court_data(shots_df, x_col, y_col)

        made_shots = shots_df[shots_df["made"] == True]
        missed_shots = shots_df[shots_df["made"] == False]

        ax.scatter(
            made_shots[x_col],
            made_shots[y_col],
            c="blue",
            edgecolors="w",
            s=50,
            alpha=0.75,
            label="Field Goal Made (FGM)",
        )
        ax.scatter(
            missed_shots[x_col],
            missed_shots[y_col],
            c="red",
            marker="x",
            s=50,
            alpha=0.75,
            label="Field Goal Missed (FGX)",
        )

        for region, polygon in ShotRegionUtil.regions.items():
            if region in ["BEYOND_HALFCOURT"]:
                continue
            patch = MplPolygon(
                list(polygon.exterior.coords),
                closed=True,
                edgecolor="k",
                fill=True,
                facecolor=ShotRegionUtil.region_colors.get(region, "#FFFFFF"),
                alpha=0.3,
                linewidth=1.5,
                linestyle="--",
            )
            ax.add_patch(patch)
            centroid = polygon.centroid
            ax.text(
                centroid.x,
                centroid.y,
                region,
                color="black",
                ha="center",
                va="center",
                fontsize=10,
            )

        ax.legend(loc="upper left")
        VisUtil.set_halfcourt(ax)
        plt.show()

    def plot_hexmap_from_df(hexmap_df):
        # Setup the plot - adjust figsize if needed
        fig, ax = plt.subplots(figsize=(12, 11))
        VisUtil.setup_court(ax)
        VisUtil.set_halfcourt(ax)

        # Create a hexbin plot
        plt.hexbin(
            hexmap_df["x"],
            hexmap_df["y"],
            C=hexmap_df["density"],
            gridsize=50,
            cmap="viridis",
            reduce_C_function=np.sum,
        )
        plt.colorbar(label="Density")

        # Adding labels and title
        plt.title("Hexmap Density Visualization")

        # Show the plot
        plt.show()

    def plot_auc(y_true, y_pred, title="ROC Curve"):
        # Compute ROC curve and ROC area
        fpr, tpr, thresholds = roc_curve(y_true, y_pred)
        roc_auc = auc(fpr, tpr)

        # Plot ROC curve
        plt.figure()
        plt.plot(
            fpr,
            tpr,
            color="darkorange",
            lw=2,
            label="ROC curve (area = %0.2f)" % roc_auc,
        )
        plt.plot([0, 1], [0, 1], color="navy", lw=2, linestyle="--")
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(title)
        plt.legend(loc="lower right")
        plt.show()

    @classmethod
    def plot_rebounds_above_expected(
        cls, rebound_stats_df, min_opportunities: int = 50
    ):
        # Position group function remains the same
        def position_group(pos):
            if pos in ["G", "G-F"]:
                return "Guards"
            elif pos in ["F", "F-C", "F-G"]:
                return "Wings"
            elif pos in ["C", "C-F"]:
                return "Bigs"
            else:
                return "Other"

        # Data preparation with custom position group ordering
        df_filtered = rebound_stats_df[rebound_stats_df["total_opportunities"] >= min_opportunities]
        df_filtered["position_group"] = df_filtered["position"].apply(position_group)
        df_filtered["net_rebounds"] = (
            df_filtered["actual_rebounds"] - df_filtered["expected_rebounds"]
        )

        # Create categorical type with custom ordering
        position_order = ["Bigs", "Wings", "Guards"]
        df_filtered["position_group"] = pd.Categorical(
            df_filtered["position_group"], 
            categories=position_order, 
            ordered=True
        )

        # Sort with custom position order
        df_filtered = df_filtered.sort_values(
            ["position_group", "rebounds_above_expected"], 
            ascending=[True, False]
        )

        # Create figure and primary axis
        fig, ax1 = plt.subplots(figsize=(20, 12))

        # Colors setup remains the same
        colors = ["#FF4136", "#FFA07A", "#98FB98", "#2ECC40"]
        n_bins = 100
        cmap = LinearSegmentedColormap.from_list("custom", colors, N=n_bins)
        norm = plt.Normalize(
            df_filtered["net_rebounds"].min(), df_filtered["net_rebounds"].max()
        )

        # Create bars
        x = np.arange(len(df_filtered))
        ax1.bar(
            x,
            df_filtered["net_rebounds"],
            width=0.8,
            color=cmap(norm(df_filtered["net_rebounds"])),
        )

        # Center the primary y-axis around zero
        max_abs_y1 = max(
            abs(df_filtered["net_rebounds"].min()),
            abs(df_filtered["net_rebounds"].max()),
        ) * 1.05
        ax1.set_ylim(-max_abs_y1, max_abs_y1)

        # Add vertical lines and group labels
        prev_group = None
        for i, group in enumerate(df_filtered["position_group"]):
            if group != prev_group:
                ax1.axvline(x=i - 0.4, color="black", linestyle="--", alpha=0.3)
                if prev_group is not None:
                    ax1.text(
                        (i + last_i) / 2,
                        ax1.get_ylim()[1] * 0.95,
                        prev_group,
                        ha="center",
                        va="bottom",
                        fontsize=14
                    )
                last_i = i
            prev_group = group

        # Add last group label and line
        ax1.axvline(x=len(df_filtered) - 0.4, color="black", linestyle="--", alpha=0.3)
        ax1.text(
            (len(df_filtered) + last_i) / 2,
            ax1.get_ylim()[1] * 0.95,
            prev_group,
            ha="center",
            va="bottom",
            fontsize=14
        )

        # Customize primary axis
        ax1.set_ylabel("Net Rebounds (Actual - Expected)", fontsize=14)
        ax1.axhline(y=0, color="black", linestyle="-", linewidth=0.5)

        # X-axis labels
        plt.xticks(
            x,
            [
                f"{row['first_name'][0]}. {row['last_name']}"
                for _, row in df_filtered.iterrows()
            ],
            rotation=45,
            ha="right",
            fontsize=10,
        )

        # Secondary axis with broken lines between groups
        ax2 = ax1.twinx()
        prev_group = None
        line_x = []
        line_y = []

        for i, (_, row) in enumerate(df_filtered.iterrows()):
            if prev_group is None or row["position_group"] == prev_group:
                line_x.append(i)
                line_y.append(row["rebounds_above_expected"])
            else:
                ax2.plot(
                    line_x,
                    line_y,
                    color="blue",
                    linewidth=3,
                    linestyle='dotted',
                    label="Rebound Rate Above Expected" if i == 1 else "",
                )
                line_x = [i]
                line_y = [row["rebounds_above_expected"]]
            prev_group = row["position_group"]

        if line_x:
            ax2.plot(line_x, line_y, color="blue", linewidth=3, linestyle='dotted',)

        # Center the secondary y-axis around zero
        max_abs_y2 = max(
            abs(df_filtered["rebounds_above_expected"].min()),
            abs(df_filtered["rebounds_above_expected"].max()),
        ) * 1.05
        ax2.set_ylim(-max_abs_y2, max_abs_y2)

        # Format y-axis ticks as percentages
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: '{:.1%}'.format(y)))
        ax2.set_ylabel('Rebound Rate Above Expected', color='blue', fontsize=14)
        ax2.tick_params(axis='y', labelcolor='blue')
        
        # For the primary y-axis (net rebounds)
        ax1.set_yticklabels([tick for tick in ax1.get_yticks()], fontsize=12)  # change font size
        ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'+{y:.1f}' if y > 0 else f'{y:.1f}'))

        # For the secondary y-axis (rebound rate)
        ax2.set_yticklabels([tick for tick in ax2.get_yticks()], fontsize=12)  # change font size
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'+{y:.1%}' if y > 0 else f'{y:.1%}'))

        # Legends and title
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=10)

        plt.title(
            f"Net Expected Rebounds & Rebound Rate Above Expected by Position\n(min {min_opportunities}+ Opportunities)",
            fontsize=20,
            pad=20,
        )
        plt.tight_layout()
        plt.show()

    @classmethod
    def plot_expected_rebounds(
        cls, rebound_stats_df, min_opportunities: int = 60
    ):
        # Filter for 65+ opportunities and sort by expected rebounds
        df_filtered = rebound_stats_df[rebound_stats_df['total_opportunities'] >= min_opportunities]
        df_filtered = df_filtered.sort_values('rebounds_above_expected', ascending=False)

        # Create figure and primary axis
        fig, ax1 = plt.subplots(figsize=(20, 12))

        # Set positions
        x = range(len(df_filtered))

        # Create custom colormap for expected rebounds (single color gradient, e.g., shades of green)
        colors = ['#B2EBF2', '#004D40']  # Light teal to dark teal
        n_bins = 100
        cmap = LinearSegmentedColormap.from_list('custom', colors, N=n_bins)

        # Normalize color values based on expected rebounds
        norm = plt.Normalize(df_filtered['expected_rebounds'].min(), df_filtered['expected_rebounds'].max())

        # Create bars on primary axis with color gradient based on expected rebounds
        ax1.bar(x, df_filtered['expected_rebounds'], width=0.8, 
                    color=cmap(norm(df_filtered['expected_rebounds'])))

        # Set the y-axis label for expected rebounds (actual values, not percentages)
        ax1.set_ylabel('Expected Rebounds', fontsize=16)
        ax1.set_yticklabels([tick for tick in ax1.get_yticks()], fontsize=12)  # Convert ticks to percentages
        ax1.axhline(y=0, color='black', linestyle='-', linewidth=0.5)

        # Customize x-axis with angled labels
        plt.xticks(x, [f"{row['first_name'][0]}. {row['last_name']}" for _, row in df_filtered.iterrows()],
                rotation=45, ha='right', fontsize=12)

        # Create secondary axis for the rebound rate line (in percentage)
        ax2 = ax1.twinx()
        ax2.plot(x, df_filtered['rebounds_above_expected'] * 100,  # Convert to percentage
                color='purple', linestyle='dotted', linewidth=5, label='RROE')  # Change line to gray and dotted
        ax2.set_ylabel('Rebound Rate Over Expected (%)', color='purple', fontsize=16)
        ax2.tick_params(axis='y', labelcolor='purple')
        ax2.set_yticklabels([f'{int(tick)}%' for tick in ax2.get_yticks()], fontsize=12)  # Convert ticks to percentages

        # Combine legends and increase font size of legend
        lines1, labels1 = ax1.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right', fontsize=16)  # Increase legend font size

        plt.title(f'Expected Rebounds and Rebound Rate Over Expected by Player\n({min_opportunities}+ Opportunities)', fontsize=20)
        plt.tight_layout()
        plt.show()