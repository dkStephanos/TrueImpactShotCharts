# The code in this file was lifted and modified. The original source author/repo: https://github.com/linouk23/NBA-Player-Movements
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML
from matplotlib import animation
from matplotlib.patches import Circle
from typing import List, Dict, Tuple
from code.io.TrackingProcessor import TrackingProcessor

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

    def __init__(self, tracking_df: pd.DataFrame):
        plt.ioff()
        self.tracking_df: pd.DataFrame = tracking_df
        team_ids = tracking_df["teamId"].head(25).dropna().unique()
        self.home_team_id = team_ids[0]
        self.away_team_id = team_ids[1]
        self.home_team_tuple = (self.TEAM_COLOR_DICT[team_ids[0]][1], self.TEAM_COLOR_DICT[team_ids[0]][0])
        self.away_team_tuple = (self.TEAM_COLOR_DICT[team_ids[1]][1], self.TEAM_COLOR_DICT[team_ids[1]][0])

        players_df = pd.read_csv("data/src/basic_player_info.csv", dtype={'person_id': str, 'jersey_num': str})
        self.players_dict = {row['person_id']: (f"{row['nickname'][0]}. {row['last_name']}", row['jersey_num']) for index, row in players_df.iterrows()}
        
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

        # Collect home and away player_ids (ball has a teamId of -1)
        players_df = moments_df.loc[moments_df['teamId'] != -1, ['playerId', 'playerName', 'teamId']].drop_duplicates()
        home_players_ids = list(players_df.loc[players_df["teamId"] == self.home_team_id]["playerId"].unique())
        away_players_ids = list(players_df.loc[players_df["teamId"] == self.away_team_id]["playerId"].unique())
        all_players_ids = home_players_ids + away_players_ids

        # Create player cell entries
        home_players = [
            " #".join([self.players_dict[player_id][0], str(self.players_dict[player_id][1])])
            for player_id in home_players_ids
        ]
        away_players = [
            " #".join([self.players_dict[player_id][0], str(self.players_dict[player_id][1])])
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
                xy=(0, 0),  # Initial position; this should be updated dynamically in the animation loop
                color="w",
                horizontalalignment="center",
                verticalalignment="center",
                fontweight="bold"
            )
            for player_id in all_players_ids
        }
        
        # Set up and add circles for the players and ball
        self.player_circles = {
            player_id: Circle(
                (0, 0),  # Initial position; this should be updated dynamically
                self.PLAYER_CIRCLE_SIZE,
                color=self.TEAM_COLOR_DICT[self.home_team_id if player_id in home_players_ids else self.away_team_id][0]  # Team color based on player's team
            )
            for player_id in all_players_ids
        }
        
        self.ball_circle = Circle(
            (0, 0),  # Initial ball position
            self.PLAYER_CIRCLE_SIZE,
            color="#ff8c00"  # Hardcoded orange for the ball
        )

        # Add all player circles and the ball circle to the axes
        for circle in self.player_circles.values():
            self.ax.add_patch(circle)
        self.ax.add_patch(self.ball_circle)

        # First, add a frame_id to group on
        moments_df = moments_df.copy()
        moments_df.loc[:, 'frame_id'] = moments_df['wcTime'].factorize()[0]
        
        
        # Include ball data and player data without filtering out the ball prematurely
        player_frames = moments_df.drop(columns=['gameId', 'teamAbbr', 'gameDate'])  # Keep ball data

        # Precompute player data for each frame, ensure to separate ball data here
        player_data_by_frame = player_frames[player_frames['teamId'] != -1].groupby('frame_id').apply(
            lambda df: df[['playerId', 'x', 'y', 'z']].to_dict(orient='records')
        )

        # Separately handle ball data to ensure it's correctly processed
        ball_data_by_frame = player_frames[player_frames['teamId'] == -1].groupby('frame_id').apply(
            lambda df: df[['x', 'y', 'z']].iloc[0].to_dict()
        )

        # Now create the precomputed_data list
        precomputed_data = [
            {
                'quarter': frame['period'].iloc[0],  # Assuming period is the same for all rows in the same frame
                'game_clock': frame['gcTime'].iloc[0],
                'shot_clock': frame['scTime'].iloc[0],
                'ball': {
                    'x': ball_data_by_frame.loc[idx]['x'],
                    'y': ball_data_by_frame.loc[idx]['y'],
                    'z': ball_data_by_frame.loc[idx]['z']
                },
                'players': player_data_by_frame.loc[idx]
            }
            for idx, frame in player_frames.groupby('frame_id')
        ]

        return precomputed_data, annotations, clock_info

    def animate(self, frame: int, precomputed_data, annotations, clock_info):
        moment = precomputed_data[frame]

        # Update the game and shot clock display
        clock_info.set_text(
            f"Quarter {moment['quarter']}\n{int(moment['game_clock']) // 60:02d}:{int(moment['game_clock']) % 60:02d}\n{moment['shot_clock']:.1f}"
        )

        # Update player positions and annotations using player IDs as dictionary keys
        updated_artists = [self.ball_circle, clock_info]

        for player in moment['players']:
            player_id = player['playerId']  # Assuming each player dictionary has an 'id' key
            if player_id in annotations:
                self.player_circles[player_id].center = (player['x'], player['y'])
                annotations[player_id].set_position((player['x'], player['y']))
                updated_artists.extend([self.player_circles[player_id], annotations[player_id]])

        # Update the ball's position and radius
        self.ball_circle.center = (moment['ball']['x'], moment['ball']['y'])
        self.ball_circle.radius = moment['ball']['z'] / self.NORMALIZATION_COEF
        
        return updated_artists

    def _create_animation(self, possession, interval: int):
        """Support method for display/save methods with caching support."""
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        moments_df = TrackingProcessor.extract_possession_moments(self.tracking_df, possession)
        precomputed_data, annotations, clock_info = self.setup_animation(moments_df)

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
        anim = self._create_animation(
            possession=possession, interval=40
        )
        return HTML(anim.to_html5_video())

    def save_animation(self, possession, filename='animation.mp4'):
        """Save the animation for the specified possession number to a file."""
        anim = self._create_animation(
            possession=possession, interval=40
        )  # Create the animation

        # Check the filename extension to decide on writer
        if filename.endswith('.gif'):
            writer = animation.PillowWriter(fps=25)
        else:
            # This requires having ffmpeg installed
            writer = 'ffmpeg'  # Default writer for MP4 and AVI
        
        # Save the animation
        anim.save(filename, writer=writer, dpi=80)  # You can adjust the DPI based on your resolution needs
