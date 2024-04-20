import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle, Arc

class GraphUtil:

    @staticmethod
    def draw_court(ax=None, color="gray", lw=1, zorder=0):
        """
        Draw basketball court lines on a Matplotlib Axes.
        """
        if ax is None:
            ax = plt.gca()

        # Define court elements
        court_elements = [
            Rectangle((0, -50), 94, 50, linewidth=lw, color=color, fill=False, zorder=zorder),  # Court outline
            Circle((5.25, -25), 0.75, linewidth=lw, color=color, fill=False, zorder=zorder),   # Left hoop
            Circle((88.75, -25), 0.75, linewidth=lw, color=color, fill=False, zorder=zorder),  # Right hoop
            Rectangle((4, -28), 0, 6, linewidth=lw, color=color, zorder=zorder),               # Left backboard
            Rectangle((90, -28), 0, 6, linewidth=lw, color=color, zorder=zorder),              # Right backboard
            Rectangle((0, -31), 19, 12, linewidth=lw, color=color, fill=False, zorder=zorder), # Left paint area
            Rectangle((75, -31), 19, 12, linewidth=lw, color=color, fill=False, zorder=zorder),# Right paint area
            Arc((19, -25), 12, 12, theta1=0, theta2=360, linewidth=lw, color=color, zorder=zorder),   # Left free throw circle
            Arc((75, -25), 12, 12, theta1=0, theta2=360, linewidth=lw, color=color, zorder=zorder),   # Right free throw circle
            Arc((47, -25), 12, 12, theta1=0, theta2=360, linewidth=lw, color=color, zorder=zorder, linestyle='dashed'),  # Center circle
        ]

        # Add the court elements onto the axes
        for element in court_elements:
            ax.add_patch(element)

        ax.set_xlim(0, 94)
        ax.set_ylim(-50, 0)
        ax.set_aspect('equal')
        ax.axis('off')  # Hide axis
        return ax

    @staticmethod
    def plot_player_movement(player_data):
        """
        Plot a single player's movements on the basketball court.
        """
        fig, ax = plt.subplots(figsize=(15, 7.5))
        ax.scatter(player_data['x'], player_data['y'], c=player_data['gcTime'], cmap='cool', edgecolors='k', zorder=5)
        cbar = plt.colorbar(ax.collections[0], ax=ax, orientation='horizontal')
        cbar.set_label('Game Clock')

        GraphUtil.draw_court(ax)
        plt.show()

    @staticmethod
    def display_full_court():
        """
        Display a full basketball court.
        """
        fig, ax = plt.subplots()
        GraphUtil.draw_court(ax)
        plt.show()

    @staticmethod
    def display_half_court():
        """
        Display a half basketball court.
        """
        fig, ax = plt.subplots()
        GraphUtil.draw_court(ax)
        ax.set_xlim(0, 50)  # Adjust as per half-court dimensions
        plt.show()

    @staticmethod
    def save_half_court(filepath):
        """
        Save a half basketball court diagram to a file.
        """
        fig, ax = plt.subplots()
        GraphUtil.draw_court(ax)
        ax.set_xlim(0, 50)  # Adjust as per half-court dimensions
        plt.savefig(filepath)
        plt.close(fig)
