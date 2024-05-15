# TrueImpactShotCharts
Integrating Rebounds and Transition Dynamics into NBA True Shot Value Analysis

![image](https://github.com/dkStephanos/TrueImpactShotCharts/blob/main/data/img/app/header.webp)



Data Preparation:

Parse Raw Data: Begin by organizing the raw tracking and play-by-play data. Ensure you understand the structure and the type of information available.
Integration with Play-by-Play Data (Optional): Decide whether to integrate play-by-play data for deeper insights or use online stats as constants for PPP in transition and off-rebounds.

Feature Generation:

Transition Defense Indicator: Develop a method to assess whether the defense has successfully transitioned based on missed field goals and shot locations.
    -> This will be the 'zone of death' metric, essentially checking if the 2 lead defenders cross halfcourt before the ball crosses the 3pt line
Offensive Rebound Percentage: Calculate the offensive rebound percentage by shot location using the geometric model approach.

Constructing the Shot Chart:

Adapt the Sloan Paper Method: Utilize the code from the Sloan paper to generate a shot chart that accounts for free throw percentages. Adapt this code as necessary to fit your dataset.
Incorporate Shot Location Efficiency: Include calculations for expected PPP based on shot locations, transition defense effectiveness, and offensive rebound potential.

Augmented Shot Chart Creation:

Combine Features into PPP Metric: Layer together the generated features (transition defense, off-reb%, FT%) to create a comprehensive PPP metric for each shot location.
Visualization: Develop a visualization method for your augmented shot chart, highlighting the areas of the court with the highest and lowest expected PPP.

Analysis and Validation:

Team and Player Analysis: Apply your metric to team and player data to identify patterns, strengths, and weaknesses.
Validation: Compare your findings against known strategies and outcomes to validate the accuracy and usefulness of your metric.

Documentation and Presentation:

Document Assumptions and Methodology: Clearly document any assumptions made and provide a detailed explanation of your methodology for reproducibility.
Prepare a Presentation: Summarize your findings and methodology in a presentation format, highlighting key insights and potential applications of your metric.
