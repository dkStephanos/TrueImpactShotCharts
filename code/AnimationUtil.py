# The code in this file was lifted and modified. The original source author/repo: https://github.com/linouk23/NBA-Player-Movements
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import HTML
from matplotlib import animation
from matplotlib.patches import Circle
from typing import List, Dict, Tuple
from ml_nba.preprocessing.utilities.DataLoader import DataLoader


class AnimationUtil:
    INTERVAL: int = 2
    COURT_DIMS: Tuple[int, int, int, int] = (
        0,
        100,
        0,
        50,
    )  # Court dimensions: X_MIN, X_MAX, Y_MIN, Y_MAX
    COL_WIDTH: float = 0.3
    SCALE: float = 1.65
    FONTSIZE: int = 6
    NORMALIZATION_COEF: float = (
        7  # Define the normalization coefficient for the ball radius
    )
    PLAYER_CIRCLE_SIZE: float = 12 / NORMALIZATION_COEF
    DIFF: int = 6
    X_CENTER: float = COURT_DIMS[1] / 2 - DIFF / 1.5 + 4.10
    Y_CENTER: float = COURT_DIMS[3] - DIFF / 1.5 - 0.35

    def __init__(self, game_df: pd.DataFrame):
        plt.ioff()
        self.game_df: pd.DataFrame = game_df
        self.teams_data = DataLoader.get_teams_data(game_df)
        self.team_color_dict = {
            self.teams_data["home_team"]["team_id"]:  self.teams_data["home_team"]["color"],
            self.teams_data["away_team"]["team_id"]:  self.teams_data["away_team"]["color"]
        }
        self.players_dict = DataLoader.get_players_dict(game_df)
        self.fig, self.ax = None, None
        self.last_animation = {}  # To store the reference to the last animation, outer dict key is interval, inner is event_num
        self.court = plt.imread("/app/static/ml_nba/imgs/fullcourt.png")

    def extract_event_moments(self, event_num: int) -> List[Dict]:
        """Extract moments for the specified event number from the game DataFrame."""
        event = next(
            (e for e in self.game_df["events"] if e["eventId"] == str(event_num)), None
        )
        if event is None:
            raise ValueError(f"Event number {event_num} not found in the dataset.")
        return event["moments"]

    def setup_animation(self, start_moment):
        """Configure the matplotlib figure and axes for the animation.""" 
        x_min, x_max, y_min, y_max = self.COURT_DIMS
        self.ax.set_xlim(x_min, x_max)
        self.ax.set_ylim(y_min, y_max)
        self.ax.axis("off")

        # Display the court image
        self.ax.imshow(self.court, zorder=0, extent=[x_min, x_max, y_min, y_max])
        self.ax.set_aspect('equal', 'box')

        # Prepare table
        column_labels = tuple(
            [self.teams_data["home_team"]["name"], self.teams_data["away_team"]["name"]]
        )
        column_colours = tuple(
            [
                self.teams_data["home_team"]["color"],
                self.teams_data["away_team"]["color"],
            ]
        )
        cell_colours = [column_colours for _ in range(5)]


        players = start_moment[5][1:]
        home_players = [
            " #".join(
                [self.players_dict[player[1]][0], self.players_dict[player[1]][1]]
            )
            for player in players[:5]
        ]
        guest_players = [
            " #".join(
                [self.players_dict[player[1]][0], self.players_dict[player[1]][1]]
            )
            for player in players[5:]
        ]
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
        
        annotations = [
            self.ax.annotate(
                self.players_dict[player[1]][1],
                xy=[0, 0],
                color="w",
                horizontalalignment="center",
                verticalalignment="center",
                fontweight="bold",
            )
            for player in start_moment[5][1:]
        ]

        # Finally set up and add circles for the players and ball
        self.player_circles = [
            Circle((0, 0), self.PLAYER_CIRCLE_SIZE, color=self.team_color_dict[player[0]])
            for player in start_moment[5][1:]
        ]
        self.ball_circle = Circle(
            (0, 0), self.PLAYER_CIRCLE_SIZE, color="#ff8c00"
        )  # Hardcoded orange
        
        for circle in self.player_circles:
            self.ax.add_patch(circle)
        self.ax.add_patch(self.ball_circle)

        return annotations, clock_info

    def animate(self, frame: int, moments, annotations, clock_info):
        """Update the positions of players, the ball, and annotations for each frame."""
        moment = moments[frame]
        quarter = moment[0]  # Hardcoded position for quarter in json
        game_clock = moment[2]  # Hardcoded position for game_clock in json
        shot_clock = moment[3]  # Hardcoded position for shot_clock in json
        ball = {"x": moment[5][0][2], "y": moment[5][0][3], "radius": moment[5][0][4]}
        players = moment[5][1:]  # Hardcoded position for players in json
        players = [{"id": player[1], "x": player[2], "y": player[3]} for player in players]
        
        self.ball_circle.center = ball["x"], ball["y"]
        self.ball_circle.radius = ball["radius"] / self.NORMALIZATION_COEF
        
        clock_info.set_text(
            "Quarter {:d}\n {:02d}:{:02d}\n {:03.1f}".format(
                quarter,
                int(game_clock) % 3600 // 60,
                int(game_clock) % 60,
                shot_clock if shot_clock else 0.0,
            )
        )

        updated_artists = [self.ball_circle, clock_info]
        for j, circle in enumerate(self.player_circles):
            if j < len(players):  # Check to avoid IndexError, some moments are missing a player
                circle.center = players[j]["x"], players[j]["y"]
                updated_artists.append(self.player_circles[j])  # Add player circle to list of updated artists
                
                # Update annotations (e.g., player jersey numbers) if you have them
                annotations[j].set_position(circle.center)
                updated_artists.append(annotations[j])  # Add annotation to list of updated artists

        return updated_artists
    
    def _create_animation(self, event_num: int, interval: int):
        """Support method for display/save methods with caching support."""
        self.fig, self.ax = plt.subplots(figsize=(12, 8))
        moments = self.extract_event_moments(event_num)
        annotations, clock_info = self.setup_animation(
            moments[0]
        )

        return animation.FuncAnimation(
            self.fig,
            self.animate,
            fargs=(moments, annotations, clock_info),
            frames=len(moments),
            interval=interval,
            blit=True
        )
        
    def display_animation(self, event_num: int):
        """Configure and display the animation for the specified event number. Designed for inline Jupyter cells"""
        anim = self._create_animation(event_num=event_num, interval=50)  # To ensure the animation is created      
        return HTML(anim.to_html5_video())

    def save_animation(
        self,
        event_num: int,
        filename: str = "play.gif",
        fps: int = 20,
        writer_option: str = "pillow",
        bitrate: int = 800,
    ):
        """Save the animation for the specified event number. Defaults to pillow writer/gif format"""
        anim = self._create_animation(event_num=event_num, interval=2)  # To ensure the animation is created

        Writer = animation.writers[writer_option]
        writer = Writer(fps=fps, metadata=dict(artist="Me"), bitrate=bitrate)
        anim.save(filename, writer=writer)
