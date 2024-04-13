# The code in this file was lifted and modified. The original source author/repo: https://github.com/linouk23/NBA-Player-Movements
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML
from matplotlib import animation
from matplotlib.patches import Circle
from typing import List, Dict, Tuple
from .TrackingProcessor import TrackingProcessor

class AnimationUtil:
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
        1610612737: "#E13A3E",
        1610612738: "#008348",
        1610612751: "#061922",
        1610612766: "#1D1160",
        1610612741: "#CE1141",
        1610612739: "#860038",
        1610612742: "#007DC5",
        1610612743: "#4D90CD",
        1610612765: "#006BB6",
        1610612744: "#FDB927",
        1610612745: "#CE1141",
        1610612754: "#00275D",
        1610612746: "#ED174C",
        1610612747: "#552582",
        1610612763: "#0F586C",
        1610612748: "#98002E",
        1610612749: "#00471B",
        1610612750: "#005083",
        1610612740: "#002B5C",
        1610612752: "#006BB6",
        1610612760: "#007DC3",
        1610612753: "#007DC5",
        1610612755: "#006BB6",
        1610612756: "#1D1160",
        1610612757: "#E03A3E",
        1610612758: "#724C9F",
        1610612759: "#BAC3C9",
        1610612761: "#CE1141",
        1610612762: "#00471B",
        1610612764: "#002B5C",
    }

    def __init__(self, tracking_df: pd.DataFrame):
        plt.ioff()
        self.tracking_df: pd.DataFrame = tracking_df
        team_ids = tracking_df["teamId"].head(25).dropna().unique()
        team_abrv = tracking_df["teamId"].head(25).dropna().unique()
        self.home_team_id = team_ids[0]
        self.away_team_id = team_ids[1]
        self.home_team_tuple = (team_abrv[0], self.TEAM_COLOR_DICT[team_ids[0]])
        self.away_team_tuple = (team_abrv[1], self.TEAM_COLOR_DICT[team_ids[1]])

        players_df = pd.read_csv("data/src/basic_player_info.csv", dtype={'person_id': str, 'jersey_num': str})
        self.players_dict = {row['person_id']: (f"{row['nickname']} {row['last_name']}", row['jersey_num']) for index, row in players_df.iterrows()}
        
        self.fig, self.ax = None, None
        self.last_animation = (
            {}
        )  # To store the reference to the last animation, outer dict key is interval, inner is event_num
        self.court = plt.imread("data/img/fullcourt.png")

    def setup_animation(self, moments_df):
        """Configure the matplotlib figure and axes for the animation."""
        x_min, x_max, y_min, y_max = self.COURT_DIMS
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.axis("off")

        # Display the court image
        self.ax.imshow(self.court, zorder=0, extent=[x_min, x_max, y_min, y_max])
        self.ax.set_aspect("equal", "box")

        # Prepare table
        column_labels = tuple([self.home_team_tuple[0], self.away_team_tuple[0]])
        column_colours = tuple(
            [
                self.home_team_tuple[1],
                self.away_team_tuple[1],
            ]
        )
        cell_colours = [column_colours for _ in range(5)]

        # Collect home and away player_ids
        players_df = moments_df.loc[moments_df['playerId'] != -1, ['playerId', 'playerName', 'teamId']].drop_duplicates()
        home_players_ids = players_df.loc[players_df["teamId"] == self.home_team_id]["playerId"].unique()
        guest_players_ids = players_df.loc[players_df["teamId"] == self.away_team_id]["playerId"].unique()

        # Create player cell entries
        home_players = [
            " #".join([self.players_dict[player_id][0], str(self.players_dict[player_id][1])])
            for player_id in home_players_ids
        ]
        guest_players = [
            " #".join([self.players_dict[player_id][0], str(self.players_dict[player_id][1])])
            for player_id in guest_players_ids
        ]
        
        # Render and scale the table
        table = plt.table(
            cellText=list(zip(home_players, guest_players)),
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
            xy=[self.X_CENTER, self.Y_CENTER],
            color="black",
            horizontalalignment="center",
            verticalalignment="center",
        )
        
        # Set up annotations for players dynamically based on current player positions in the frame
        annotations = {
            player_id: self.ax.annotate(
                f"{self.players_dict[player_id][0]} #{self.players_dict[player_id][1]}",  # Player name and jersey_num
                xy=(0, 0),  # Initial position; this should be updated dynamically in the animation loop
                color="w",
                horizontalalignment="center",
                verticalalignment="center",
                fontweight="bold"
            )
            for player_id in self.players_dict
        }
        
        print(annotations)

        # Set up and add circles for the players and ball
        self.player_circles = [
            Circle(
                (0, 0),  # Initial position; this should be updated dynamically
                self.PLAYER_CIRCLE_SIZE,
                color=self.TEAM_COLOR_DICT[self.home_team_id if player_id in home_players_ids else self.away_team_id]  # Team color based on player's team
            )
            for player_id in self.players_dict
        ]
        self.ball_circle = Circle(
            (0, 0),  # Initial ball position
            self.PLAYER_CIRCLE_SIZE,
            color="#ff8c00"  # Hardcoded orange for the ball
        )

        # Add all player circles and the ball circle to the axes
        for circle in self.player_circles:
            self.ax.add_patch(circle)
        self.ax.add_patch(self.ball_circle)
        
        precomputed_data = [{
            'quarter': row['period'],
            'game_clock': row['gcTime'],
            'shot_clock': row['scTime'],
            'ball': {'x': row['x'], 'y': row['y'], 'radius': row['z'] if 'z' in row else 0.4},
            'players': moments_df[moments_df['wcTime'] == row['wcTime']].to_dict(orient='records')
        } for index, row in moments_df.iterrows()]

        return precomputed_data, annotations, clock_info

    def animate(self, frame: int, precomputed_data, annotations, clock_info):
        moment = precomputed_data[frame]

        # Update the ball's position and radius
        self.ball_circle.center = (moment['ball']['x'], moment['ball']['y'])
        self.ball_circle.radius = moment['ball']['radius']

        # Update the game and shot clock display
        clock_info.set_text(
            f"Quarter {moment['quarter']}\n{int(moment['game_clock']) // 60:02d}:{int(moment['game_clock']) % 60:02d}\n{moment['shot_clock']:.1f}"
        )

        # Update player positions and annotations
        updated_artists = [self.ball_circle, clock_info]
        for j, player in enumerate(moment['players']):
            # Assuming self.player_circles and annotations are pre-initialized to the correct length
            self.player_circles[j].center = (player['x'], player['y'])
            annotations[j].set_text(f"{player['name']} #{player['jersey']}")
            annotations[j].set_position((player['x'], player['y']))
            updated_artists.extend([self.player_circles[j], annotations[j]])

        return updated_artists

    def _create_animation(self, event, interval: int):
        """Support method for display/save methods with caching support."""
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        moments_df = TrackingProcessor.extract_possession_moments(self.tracking_df, event)
        precomputed_data, annotations, clock_info = self.setup_animation(moments_df)

        return animation.FuncAnimation(
            self.fig,
            self.animate,
            fargs=(precomputed_data, annotations, clock_info),
            frames=len(moments_df),
            interval=interval,
            blit=True,
        )

    def display_animation(self, event):        
        """Configure and display the animation for the specified event number. Designed for inline Jupyter cells"""
        anim = self._create_animation(
            event=event, interval=50
        )  # To ensure the animation is created
        return HTML(anim.to_html5_video())

    def save_animation(
        self,
        event,
        filename: str = "play.gif",
        fps: int = 20,
        writer_option: str = "pillow",
        bitrate: int = 800,
    ):
        """Save the animation for the specified event number. Defaults to pillow writer/gif format"""
        anim = self._create_animation(
            event=event, interval=25
        )  # To ensure the animation is created

        Writer = animation.writers[writer_option]
        writer = Writer(fps=fps, metadata=dict(artist="Me"), bitrate=bitrate)
        anim.save(filename, writer=writer)
