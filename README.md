# Neuroglancer Benchmark for Automated Proofreading

The pipeline for obtaining full connectomes (brain wirings) is steadily being automated. Starting with electron microscopy images, segmentation models generate 3D neuron reconstructions. However, even with superhuman precision, some neurons contain errors.  

Currently, human proofreaders manually detect and correct these errors using a Web Interface called **Neuroglancer**. This process is **unscalable**. We need **intelligent agents** capable of making human-level proofreading decisions and applying them within Neuroglancer to assist our teams.  

The **Neuroglancer environment** presents several challenges. While the ultimate goal is fully automated proofreading, intermediate tasks such as **efficient neuron navigation, error detection, and synapse identification** can contribute to progress.  

## Understanding the Setup

- **[Flywire Tutorial](https://ngl.flywire.ai/)**: Provides access to neurons in a Neuroglancer-like environment, including a proofreading tutorial.  

## Example Videos  

### 1. Human Proofreader in Action  
A proofreader manipulates a neuron, detects an **abnormal cut**, and takes corrective action.  
[![Proofreading Video](example_videos/video_1_proofreading_thumbnail.mov)](example_videos/video_1_proofreading_thumbnail.mov)  

### 2. Model Clicking on the Highest Z Position  
A trained model clicks on the **highest Z position** (blue axis) of a neuron within its field of view. The action space is limited to clicking only. Future improvements could incorporate **zooming out and changing orientation** for efficiency.  
[![Highest Z Clicker](example_videos/video_2_highest_z_clicker.mov)](example_videos/video_2_highest_z_clicker.mov)  

### 3. Programmatic Use of Neuroglancer  
Demonstrates **Neuroglancer integration with Python**, showing how the environment can be used in **reinforcement learning (RL)** setups to return images, states, and execute direct actions.  
[![Neuroglancer Environment](example_videos/video_3_environment_thumbnail.mov)](example_videos/video_3_environment_thumbnail.mov)  
