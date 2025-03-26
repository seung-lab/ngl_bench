# Neuroglancer Benchmark for Automated Proofreading

## 🧠 Overview

The pipeline to obtain full connectomes (brain wirings) is steadily being fully automated; images obtained by electron microscopy can be processed by segmentation models to then build comprehensive 3D models of individual neurons. However, despite their superhuman precision, model outputs of the reconstructed neurons bear errors. 

Currently, a team of human proofreaders are manually finding these errors on the connectome of a femla Drosophila and correcting them through a Web Interface called **Neuroglancer**, which allows for both 3D and 2D cross-section visualization of neuron data.

This is **unscalable**. Proofreaders must tediously analyze the local structure and global context of neurons to assess for errors (typically an accidental merging of neurons or separation of an individual neuron). Even for smaller connectomes, such as that of the female Drosophila, this proves to be a monumental task.

We need **Agents** capable of making human-level observations as well as decisions and applying them through the Web interface onto the neurons to help our team. This is no easy task - proofreading aside, the Neuroglancer environment is a challenge to successfully understand and utilize due to its many dynamic visual inputs. While the overall goal is fully automated proofreading, there are several intermediate challenges that agentic approachs must address such as efficiently navigating through neurons, finding errors, and finding synapses...

## ❔ Setup

### Understanding Neuroglancer

- **[Flywire Environment Tutorial](https://ngl.flywire.ai/)**: Provides access to neurons in a Neuroglancer-like environment, including a proofreading & navigation tutorial. This gives access to the neuron reconstruction of the female fly brain.
- We highly recommend revisiting **[this](ADVICE.md)** FAQ for more specific information on Neuroglancer once you have finished the setup steps below!

### Installing Neuroglancer

FlyWire is an online implementation of Neuroglancer, built to host edits by multiple proofreaders in one location. For development and testing purposes, we recommend locally installing **[Neuroglancer](https://github.com/seung-lab/neuroglancer/tree/rl-recording)** rather than using FlyWire.

See the bottom of this section for common troubleshooting advice.

1. Clone the **rl-recording** branch of Neuroglancer **[here](https://github.com/seung-lab/neuroglancer/tree/rl-recording)**.
2. Run `npm install`
3. Run `npm run build`
4. Start a local instance of Neuroglancer by running `python -m http.server --directory dist/ 8000`
5. Open [http://localhost:8000/client]() to test if your install process was successful; you should see the Neuroglancer user interface load in an empty 4-pane view.

**Note**: after successfully hosting Neuroglancer for the first time, you only need to follow steps 4-5 to host again.

#### Troubleshooting tips
- Try reinstalling Node

### Interfacing with Neuroglancer

For your convenience, we have provided a Python class containing functions that automate the initialization process and streamline action applications to Neuroglancer. Please see [here](INTEGRATION.md) for more information. 

## 📷 Example Videos

### 1. Human Proofreader in Action  
Example of a human proofreader making a sequence of actions. He detects an **abnormal cut**, explores the nearby environment and corrects the error.  

[![Proofreading Video](example_videos/gifs/video_1.gif)](example_videos/gifs/video_1.gif)  

### 2. Model Clicking on the Highest Z Position  
Example of a trained model clicks on the **highest Z position** (blue axis) of a neuron within its field of view. The action space is limited to clicking only. Future improvements could incorporate **zooming out and changing orientation** for faster navigation. Manipulating a 3D environment is a difficult task and is one of the main challenges in automated proofreading.

[![Highest Z Clicker](example_videos/gifs/video_2.gif)](example_videos/gifs/video_2.gif)  

### 3. Programmatic Use of Neuroglancer  
Existing code for **Neuroglancer integration with Python**, showing how the environment can be used in **reinforcement learning (RL)** setups to return images, states, and execute direct actions. The code  was built for fast querying by writing direct Javascript commands with Selenium.

[![Neuroglancer Environment](example_videos/gifs/video_3.gif)](example_videos/gifs/video_3.gif)  
