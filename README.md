# TrueImpactShotCharts
Integrating Rebounds and Transition Dynamics into NBA True Shot Value Analysis

![image](https://github.com/dkStephanos/TrueImpactShotCharts/blob/main/data/img/app/readme.webp)


## Overview

TrueImpactShotCharts is a basketball analytics project focused on creating advanced shot charts that incorporate true impact metrics. The project aims to provide a comprehensive analysis of shot selection, efficiency, and impact by leveraging various data visualization techniques, including topographical heatmaps and hexbin aggregation.

## Table of Contents

- [TrueImpactShotCharts](#trueimpactshotcharts)
  - [Overview](#overview)
  - [Table of Contents](#table-of-contents)
  - [Features](#features)
  - [Installation](#installation)
  - [Usage](#usage)
    - [Extract and Visualize Data](#extract-and-visualize-data)
    - [Voronoi Diagram Example](#voronoi-diagram-example)
    - [Continuous Shot Chart Example](#continuous-shot-chart-example)
  - [Data Sources](#data-sources)
  - [Contributing](#contributing)
  - [License](#license)
  - [Acknowledgements](#acknowledgements)

## Features

- **True Impact Shot Charts**: Generate detailed shot charts that incorporate true impact metrics.
- **Topographical Heatmaps**: Visualize shot data using topographical heatmaps for better insights.
- **Hexbin Aggregation**: Use hexbin aggregation to smooth out data and create more informative visualizations.
- **Rebound Statistics**: Calculate and visualize rebound statistics, including offensive and defensive rebound chances.

## Installation

```bash
git clone https://github.com/dkStephanos/TrueImpactShotCharts
cd TrueImpactShotCharts/devops
docker-compose up
```

## Usage

TrueImpactShotCharts is organized into several directories and modules to help you explore and analyze NBA tracking data efficiently. The main components include:

- `code/`: Contains all the utility classes and functions for processing and visualizing the data.
- `notebooks/`: Jupyter notebooks with step-by-step walkthroughs of the data processing, feature generation, and visualization.
- `data/`: Contains the source data files used in the analysis.

To get started, follow the examples below to see how you can leverage these utilities in your own analysis. For more comprehensive examples and interactive exploration, refer to the notebooks in the `notebooks/` directory.

### Extract and Visualize Data

```python
# Change this to any valid gameId in the source data
GAME_ID = "0022300869"

# Each source file has a dedicated processor class, use these to load and process src data
event_df = EventProcessor.load_game(GAME_ID)
tracking_df = TrackingProcessor.load_game(GAME_ID)
possession_df = PossessionProcessor.load_game(GAME_ID)

# Begin by extracting and visualizing some data
anim = VisUtil(tracking_df)
anim.display_animation(possession_df.loc[possession_df["outcome"] == "FGM"].iloc[0])
```

<p align="center">
  <img src="https://github.com/dkStephanos/TrueImpactShotCharts/blob/main/data/img/animation.gif" alt="Animation Example" />
</p>

### Voronoi Diagram Example

```python
# Extract an individual shot attempt as an example
possession = shot_rebound_classified_df.iloc[-2]
moment_df = TrackingProcessor.extract_moment_from_timestamps(tracking_df, possession['shot_time'], possession['rebound_time'])

# Instantiate the VisUtil and plot the Voronoi diagram at shot_time, cells are color coded according to the team that 'owns' them
anim = VisUtil(moment_df)
anim.plot_voronoi_at_timestamp(possession['shot_time'], possession["basketX"])
```

<p align="center">
  <img src="https://github.com/dkStephanos/TrueImpactShotCharts/blob/main/data/img/voronoi.png" alt="Voronoi Diagram Example" />
</p>

### Continuous Shot Chart Example

```python
# Plot topographical heatmap using true impact points produced
VisUtil.plot_topographical_heatmap(true_impact_points_df, weight_col="true_impact_points_produced")

# Plot topographical heatmap using points produced
VisUtil.plot_topographical_heatmap(true_impact_points_df, weight_col="points_produced")

# Plot topographical heatmap using true points produced
VisUtil.plot_topographical_heatmap(true_impact_points_df, weight_col="true_points_produced")
```

<p align="center">
  <img src="https://github.com/dkStephanos/TrueImpactShotCharts/blob/main/data/img/shot_charts/true_impact_points.png" alt="Continuous Shot Chart Example" />
</p>

For more examples and detailed explanations, please refer to the notebooks in the notebooks/ directory. These notebooks provide a step-by-step guide to using the utilities and exploring the data comprehensively.

## Data Sources

This project leverages play-by-play and tracking data from the 2023-24 NBA Regular Season. 
To comply with confidentiality, the original source data can not be shared on this repo.

## Contributing

We welcome contributions to enhance this project. To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push the branch to your forked repository.
4. Create a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

We would like to thank the following sources for their invaluable contributions to the field of basketball analytics, and inspiring this project:

- [Estimating NBA Team Shot Selection Efficiency from Aggregations of True Continuous Shot Charts](https://www.sloansportsconference.com/research-papers/estimating-nba-team-shot-selection-efficiency-from-aggregations-of-true-continuous-shot-charts-a-generalized-additive-model-approach)
- [A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes](http://www.lukebornn.com/papers/cervone_ssac_2016.pdf)
- [Offensive Crashing: Using Data to Understand and Optimize Offensive Rebounding](https://squared2020.com/2019/11/18/offensive-crashing/)
- [Extending Possessions: A Geometric Distribution Approach to Basketball Possessions](https://squared2020.com/2019/11/27/extending-possessions-geometric-distribution/)
