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

### Setting Up the Environment

1. **Set up the working directory**:
    ```python
    import os
    os.chdir('/path/to/TrueImpactShotCharts')
    ```

2. **Load and visualize shot data**:
    ```python
    import pandas as pd
    from code.util.VisUtil import VisUtil
    from code.util.FeatureUtil import FeatureUtil

    # Load the data
    data_file_path = os.path.join('data', 'src', 'events.csv')
    shot_data = pd.read_csv(data_file_path)

    # Generate and display a topographical heatmap
    VisUtil.plot_topographical_heatmap_hexbin(shot_data, x_col="shot_x", y_col="shot_y", weight_col="true_impact_points_produced")
    ```

### Rebound Statistics

1. **Calculate and display rebound statistics**:
    ```python
    from code.util.StatsUtil import StatsUtil

    # Calculate rebound statistics
    rebound_stats = StatsUtil.calculate_rebound_statistics_by_region(shot_data)
    print(rebound_stats)
    ```

## Data Sources

This project leverages data from various sources:

- [Estimating NBA Team Shot Selection Efficiency from Aggregations of True Continuous Shot Charts](https://www.sloansportsconference.com/research-papers/estimating-nba-team-shot-selection-efficiency-from-aggregations-of-true-continuous-shot-charts-a-generalized-additive-model-approach)
- [A Multiresolution Stochastic Process Model for Predicting Basketball Possession Outcomes](http://www.lukebornn.com/papers/cervone_ssac_2016.pdf)
- [Offensive Crashing: Using Data to Understand and Optimize Offensive Rebounding](https://squared2020.com/2019/11/18/offensive-crashing/)
- [Extending Possessions: A Geometric Distribution Approach to Basketball Possessions](https://squared2020.com/2019/11/27/extending-possessions-geometric-distribution/)

## Contributing

We welcome contributions to enhance this project. To contribute, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push the branch to your forked repository.
4. Create a pull request with a detailed description of your changes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

We would like to thank the following sources for their invaluable contributions to the field of basketball analytics:

- Sloan Sports Analytics Conference
- Luke Bornn and his co-authors
- Squared2020
