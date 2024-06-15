# TrueImpactShotCharts
Integrating Rebounds and Transition Dynamics into NBA True Shot Value Analysis

![image](https://github.com/dkStephanos/TrueImpactShotCharts/blob/main/data/img/app/readme.webp)


## Overview

TrueImpactShotCharts is a basketball analytics project focused on creating advanced shot charts that incorporate true impact metrics. The project aims to provide a comprehensive analysis of shot selection, efficiency, and impact by leveraging various data visualization techniques, including topographical heatmaps and hexbin aggregation.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
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

To install and run this project locally, follow these steps:

1. **Clone the repository**:
    ```sh
    git clone https://github.com/yourusername/TrueImpactShotCharts.git
    cd TrueImpactShotCharts
    ```

2. **Build the Docker container**:
    ```sh
    docker build -t trueimpactshotcharts .
    ```

3. **Run the Docker container**:
    ```sh
    docker run -p 8888:8888 trueimpactshotcharts
    ```

## Usage

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

![image](https://github.com/dkStephanos/TrueImpactShotCharts/blob/main/data/img/animation.mp4)


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
