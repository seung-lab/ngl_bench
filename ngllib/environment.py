"""
Standalone full Neuroglancer environment. Handles sending actions, getting state, changing JSON state, parsing data, screenshotting, etc.
"""

"""------------Imports-------------"""
from .utils.utils import parse_action
import time, json, copy, os, argparse, PIL, platform, base64, io, urllib
from PIL import Image, ImageDraw
from .utils.maths import quaternion_to_euler, euler_to_quaternion
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .utils.MouseActionHandler import MouseActionHandler
import os
"""--------------------------------"""

class Environment:
    def __init__(self, headless:bool=False, config_path:str='config.json', verbose:bool=False, start_url:str=None, reward_function:'function'=None):
        """
        Args:
            headless: Whether to run the Neuroglancer viewer in headless mode. If True, nothing will be displayed. May slightly alter the behavior of neuroglancer but will increase performance.
            verbose: Whether to print verbose output.
            config_path: Path to the config file.
            reward_function: Alternative reward function to use. If None, the default reward function will be used (see docs for more details).
            start_url: The URL to start the session on. If not specified, the default Neuroglancer session will be used.
        """
        self.headless = headless
        self.verbose = verbose
        self.compute_reward = reward_function or self.compute_default_reward

        # Load configuration information
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        if start_url is not None:
            self.start_url = start_url
        else:
            self.start_url = self.config['default_ngl_start_url']

        self.window_width = self.config['window_width']
        self.window_height = self.config['window_height']

        # Initialize Chrome
        self.chrome_options = self.initialize_chrome_options(headless=self.headless, window_width=self.window_width, window_height=self.window_height)
        self.chrome_service = self.initialize_chrome_service(self.chrome_options) # will initialize the service based on platform

        try:
            self.driver = webdriver.Chrome(service=self.chrome_service, options=self.chrome_options)
            self.action_handler = MouseActionHandler(self.driver)
        except Exception:
            raise Exception(f"Error initializing Chrome using Chromedriver. Validate the path to the driver in config.json or use default paths.")

    def initialize_chrome_options(self, headless:bool, window_width:int, window_height:int)->Options:
        """
        Initializes the Chrome options for the Neuroglancer viewer.

        Args:
            headless: Whether to run the Neuroglancer viewer in headless mode. If True, nothing will be displayed. May slightly alter the behavior of neuroglancer but will increase performance.
            window_width: The width of the Chrome window.
            window_height: The height of the Chrome window.
        """

        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
            #chrome_options.add_argument("--disable-gpu") provokes WebGL error
            chrome_options.add_argument("--enable-logging")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("useAutomationExtension", False)
        chrome_options.add_experimental_option("excludeSwitches",["enable-automation"])  
        chrome_options.add_argument(f"--window-size={window_width},{window_height}")   
        return chrome_options
    
    def initialize_chrome_service(self, chrome_options:Options)->None:
        """
        Returns the Chrome service for the Neuroglancer viewer based on platform with input options.
        Args:
            chrome_options: The Chrome options to use.
        """

        if platform.system() == "Darwin":  # macOS

            chrome_driver_path = self.config['driver_path_mac']
            chrome_service = Service(chrome_driver_path)
            
        elif platform.system() == "Windows":

            chrome_driver_path = self.config['driver_path_win']
            chrome_service = Service(chrome_driver_path)
            chrome_border_height = 95
            chrome_border_width = 16
            chrome_options.add_argument("--force-device-scale-factor=1")

        elif platform.system() == "Linux":
            chrome_driver_path = self.config['driver_path_linux']
            chrome_service = Service(chrome_driver_path)
            chrome_options.binary_location = self.config['chrome_binary_path_linux']
        return chrome_service
    
    def start_session(self, start_url:str=None, **options:dict)-> None:
        """
        Starts the Neuroglancer session, logging into Google and then opening Neuroglancer.
        Args:
            start_url: The URL to start the session on. If not specified, the default Neuroglancer session will be used.
            **options: Additional options to pass to the session. May include image_path, euler_angles, resize, add_mouse, fast (see docs for more info and default behavior).
        """

        self.options = options

        self.driver.get("https://accounts.google.com/Login")
        self.google_login()
        self.start_neuroglancer_session(url=start_url)

    def end_session(self)-> None:
        """
        Ends the Neuroglancer session by closing the Chrome window and quitting the driver.
        """

        self.driver.close()
        self.driver.quit()

    def google_login(self)-> None:
        """ 
        Logs into Google account using the mail address and password provided in the constructor. This is highly dependent on the Chrome versions and their updates; if this function returns errors please contact (see docs for emails).
        """
        try:
            self.driver.get('https://accounts.google.com/Login')
            email_input = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "identifierId"))
            )
            email_input.send_keys(self.config['google_email_address'])
            email_input.send_keys(Keys.RETURN)
            password_input = WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//input[@type='password']"))
            )
            password_input.send_keys(self.config['google_password'])
            password_input.send_keys(Keys.RETURN)
            if self.verbose:
                print("Login attempted. Waiting for confirmation...")
            WebDriverWait(self.driver, 20).until(EC.url_contains("myaccount.google.com"))
            if self.verbose:
                print("Login successful!")
        except Exception as e:
            raise Exception(f"Login failed: {e}")

    def start_neuroglancer_session(self, url:str=None)-> None:
        """
        Starts a Neuroglancer session. This is the most common session used for training and does not require any additional login.
        Args:
            url: The URL to start the session on. If not specified, the default Neuroglancer session will be used.
        """
        if self.verbose:
            print("Starting Neuroglancer session...")
        if url is not None:
            ngl_url = url
        else:
            ngl_url = self.config['default_ngl_start_url']
        self.change_url(ngl_url)
        if self.verbose:
            print(f"Neuroglancer session started. Navigated to URL given.")

        self.prev_state, self.prev_json = self.prepare_state()

    def start_middle_auth_session(self, start_url: str = None)-> None:
        """This will start a local Host session using Graphene segmentation. This requires passing the middle-auth login which is hard to automate. Be very careful when using this and adapt accordingly.
        Args:
            start_url: The URL to start the session on. If not specified, the default graphene session will be used.
        Returns:
            None, session is started in place on the driver instance.
        """
        try:
            if start_url is None:
                start_url = self.config['default_middle_auth_start_url']
            self.driver.get(start_url)
            wait = WebDriverWait(self.driver, 10)
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//ul[@id='statusContainerModal']//button[text()='Login']")))
            login_button.click()
            main_window = self.driver.current_window_handle
            WebDriverWait(self.driver, 10).until(lambda d: len(d.window_handles) > 1)
            for handle in self.driver.window_handles:
                if handle != main_window:
                    self.driver.switch_to.window(handle)
                    break
            pni_rlagent = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'PNI RLAgent')]"))
            )
            pni_rlagent.click()
            time.sleep(1)
            if self.headless:
                continue_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "submit_approve_access"))
                )
            else:
                continue_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//*[contains(text(), 'Continue')]"))
                )
            continue_button.click()
            self.driver.switch_to.window(main_window)
        except Exception as e:
            if self.verbose:
                print("An error occurred:", e)

    def refresh(self)-> None:
        """Refreshes the current page. Useful to force rendering of neurons."""
        self.driver.refresh()
        if self.verbose:
            print("Page refreshed.")

    def get_url(self)-> str:
        """Returns the current Neuroglancer URL."""
        return self.driver.current_url
    
    def change_url(self, user_url: str)-> None:
        """Changes the URL of the Neuroglancer viewer to user_url.
        Args:
            user_url: The URL to change to.
        """

        if self.driver:
            self.driver.get(user_url)  
        else:
            raise Exception("Driver not initialized. Please start the session first.")

    def get_screenshot(self, save_path: str = None, resize:bool=False, mouse_x:int=None, mouse_y:int=None, fast:bool=True)-> Image.Image:
        """
            Get a screenshot of the current page.
            Args:
                save_path: Path to save the image. If not specified, the image is not saved.
                resize: Boolean to resize the image. Normally we want to resize the image later on before training.
                mouse_x: X coordinate of the mouse. -> Optional, if not specified, the mouse position is not added to the image.
                mouse_y: Y coordinate of the mouse. -> Optional, if not specified, the mouse position is not added to the image.
                fast: Boolean to use the fast method to get the screenshot. If False, the slow method is used (default Selenium method).
        Returns:
            Image.Image, the screenshot of the current page as a PIL Image object.
        """

        if fast:
            screenshot_raw = self.driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "jpeg", "quality": 85})
            screenshot_bytes = base64.b64decode(screenshot_raw["data"])
            image = Image.open(io.BytesIO(screenshot_bytes))
        else:
            screenshot = self.driver.get_screenshot_as_png()
            image = Image.open(io.BytesIO(screenshot))
        if resize:
            image = image.resize((self.resize_width, self.resize_height))
        if mouse_x is not None and mouse_y is not None:
            draw = ImageDraw.Draw(image)
            #mouse_y += self.values.neuroglancer_margin_top # TODO: Make it clear how this counted. Account for the fact we record mouse position from top left of canva and not top left of window
            draw.ellipse((mouse_x - 5, mouse_y - 5, mouse_x + 5, mouse_y + 5), fill='red', outline='red')
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            image.save(save_path, format='PNG')
        return image

    def get_JSON_state(self)-> dict:
        """Parse the URL to get the JSON state
        
        Returns:
            dict: The JSON state of the Neuroglancer viewer.
        """

        script = """
        if (window.viewer && window.viewer.state) {
            return JSON.stringify(viewer.state);
        } else {
            return null;
        }
        """
        try:
            state = self.driver.execute_script(script)
            return state
        except Exception as e:
            if self.verbose:
                print("An error occurred:", e)
            return None
    
    def change_JSON_state_url(self, json_state, localHost=False)-> None:
        """Change the state of the Neuroglancer viewer by changing the part of the URL corresponding to JSON changes.

        Args:
            json_state: The JSON state to change to. Takes a dictionary or a string.
            localHost: Whether to use the local host session. Otherwise uses the Neuroglancer demo session.
        """

        try:
            if isinstance(json_state, dict):
                json_object = json_state
            else:
                json_object = json.loads(json_state)
            serialized_json = json.dumps(json_object)

            encoded_json = urllib.parse.quote(serialized_json)
            if localHost:
                new_url = f"http://localhost:8000/client/#!{encoded_json}"
            else:
                new_url = f"https://neuroglancer-demo.appspot.com/#!{encoded_json}"
            self.change_url(new_url)
        except Exception as e:
            print("An error occurred while changing the JSON state:", e)
    
    def mouse_key_action(self, x: float, y: float, action: str, keysPressed:str = "None"):
        """Executes a mouse action at a given position. Hands off actions to MouseActionHandler which executes a JavaScript action.
        Args:
            x: The x coordinate of the mouse.
            y: The y coordinate of the mouse.
            action: The action to execute.
            keysPressed: The keys to press.
        """

        self.action_handler.execute_click(x, y, action, keysPressed)

    def change_viewport_size(self, width: int, height: int):
        """
            Change the viewport size of the Neuroglancer viewer.
            Args:
                width: The width of the viewport.
                height: The height of the viewport.
        """

        self.driver.set_window_size(width, height)
    



    """Here are the functions related to Agentic Behavior"""

    def reset(self, url:str=None)->None:
        """
            Resets the environment to the default state.
            Args:
                url: The URL to reset to. If not specified, the default Neuroglancer session will be used.
        """
        if url is not None:
            self.start_neuroglancer_session(url=url)
        else:
            self.start_neuroglancer_session()
        
    def apply_actions(self, output_vector:list)->None:
        """
            Takes an action vector as deltas on the continuous values and true values for x,y clicks.
            Args:
                output_vector: The action vector to apply.
        """

        json_state = self.prev_json

        euler_angles = self.options.get('euler_angles', False)

        if euler_angles:
            (
            left_click, right_click, double_click,  # 3 booleans
            x, y,                                  # 2 floats for mouse position
            key_Shift, key_Ctrl, key_Alt,          # 3 booleans for keys
            json_change,                           # 1 boolean for JSON change
            delta_position_x, delta_position_y, delta_position_z,  # 3 floats
            delta_crossSectionScale,               # 1 float
            delta_projectionOrientation_e1, delta_projectionOrientation_e2, delta_projectionOrientation_e3,  # 3 floats
            delta_projectionScale                  # 1 float
            ) = [v for v in output_vector] # before [v.item() if isinstance(v, torch.Tensor) else v for v in output_vector]
        else:
            (
            left_click, right_click, double_click,  # 3 booleans
            x, y,                                  # 2 floats for mouse position
            key_Shift, key_Ctrl, key_Alt,          # 3 booleans for keys
            json_change,                           # 1 boolean for JSON change
            delta_position_x, delta_position_y, delta_position_z,  # 3 floats
            delta_crossSectionScale,               # 1 float
            delta_projectionOrientation_q1, delta_projectionOrientation_q2,
            delta_projectionOrientation_q3, delta_projectionOrientation_q4,  # 4 floats
            delta_projectionScale                  # 1 float
            ) = [v for v in output_vector] # before [v.item() if isinstance(v, torch.Tensor) else v for v in output_vector]
    
        # Should be redundant
        # if json_state is None:
        #     json_state = self.get_JSON_state()
        #     json_state = json.loads(json_state)

        # Process output_vector into actions to Chrome
        key_pressed = ""
        if key_Shift:
            if self.verbose:
                print("Shift key pressed")
            key_pressed += "Shift, "
        if key_Ctrl:
            if self.verbose:
                print("Ctrl key pressed")
            key_pressed += "Ctrl, "
        if key_Alt:
            if self.verbose:
                print("Alt key pressed")
            key_pressed += "Alt, "
        key_pressed = key_pressed.strip(", ")

        if left_click:
            if self.verbose:
                print("Decided to do a left click at position", x, y)
            self.mouse_key_action(x, y, "left_click", key_pressed)
        elif right_click:
            if self.verbose:
                print("Decided to do a right click at position", x, y)
            self.mouse_key_action(x, y, "right_click", key_pressed)
        elif double_click:
            if self.verbose:
                print("Decided to do a double click at position", x, y)
            self.mouse_key_action(x, y, "double_click", key_pressed)
        elif json_change:
            if self.verbose:
                print("Decided to change the JSON state")
                old_position = copy.deepcopy(json_state["position"])
                old_crossSectionScale = copy.deepcopy(json_state["crossSectionScale"])
                old_projectionScale = copy.deepcopy(json_state["projectionScale"])

            json_state["position"][0] += delta_position_x
            json_state["position"][1] += delta_position_y
            json_state["position"][2] += delta_position_z
            if self.verbose:
                print(f"Position updated: {old_position} -> {json_state['position']}")

            json_state["crossSectionScale"] += delta_crossSectionScale
            if self.verbose:
                print(f"CrossSectionScale updated: {old_crossSectionScale:.6f} -> {json_state['crossSectionScale']:.6f}")

            if euler_angles:
                old_projectionOrientation = quaternion_to_euler(json_state["projectionOrientation"])
                new_projectionOrientation = [
                    old_projectionOrientation[0] + delta_projectionOrientation_e1,
                    old_projectionOrientation[1] + delta_projectionOrientation_e2,
                    old_projectionOrientation[2] + delta_projectionOrientation_e3
                ]
                json_state["projectionOrientation"] = euler_to_quaternion(new_projectionOrientation)
            else:    
                json_state["projectionOrientation"][0] += delta_projectionOrientation_q1
                json_state["projectionOrientation"][1] += delta_projectionOrientation_q2
                json_state["projectionOrientation"][2] += delta_projectionOrientation_q3 
                json_state["projectionOrientation"][3] += delta_projectionOrientation_q4
            if self.verbose:
                print(f"ProjectionOrientation updated: {old_projectionOrientation} -> {json_state['projectionOrientation']}")

            json_state["projectionScale"] = min(500000, json_state["projectionScale"] + delta_projectionScale)
            if self.verbose:
                print(f"ProjectionScale updated: {old_projectionScale:.6f} -> {json_state['projectionScale']:.6f}")
            self.change_JSON_state_url(json_state)
        if self.verbose:
            print("Decision acted upon")
    
    def step(self, action:list)->tuple[list, float, bool, dict]:
        """ Core function. Takes in an action vector and returns JSON state and environment image.
        
        Args:
            action: The action vector to apply. This is the output of the model.
        Returns:
            state: The state of the environment after applying the action.
            reward: The reward for the action taken.
            done: Whether the episode is done or not.
            json_state: The JSON state of the Neuroglancer viewer.
        """

        self.apply_actions(action)

        state, json_state = self.prepare_state()
        
        reward, done = self.compute_reward(state, action, self.prev_state)

        self.prev_state = state
        self.prev_json = json_state

        return state, reward, done, json_state

    def compute_default_reward(self, state:list, action:list, prev_state:list)->tuple[float, bool]:
        """
            Computes the reward based on the state and the action.

            Args:
                state: The current state of the environment.
                action: The action taken.
                prev_state: The previous state of the environment.
        """

        # Extremely basic reward function based on increases in z-position.
        reward = state[0][0][2] - prev_state[0][0][2] 

        return reward, False

    def prepare_state(self)->tuple[tuple[list, PIL.Image.Image], dict]:
        """
            Core function. Returns a list for the state and the current image as a PIL image (default from ChromeNGL class)

            Returns:
                pos_state: List of position, crossSectionScale, projectionOrientation, projectionScale
                curr_image: PIL image of the current state
                json_state: JSON state of the current state as a dictionary
        """

        image_path = self.options.get('image_path', None)
        euler_angles = self.options.get('euler_angles', False)
        resize = self.options.get('resize', False)
        add_mouse = self.options.get('add_mouse', False)
        fast = self.options.get('fast', True)


        state = self.get_JSON_state()
        json_state = json.loads(state)
        position = json_state["position"]
        crossSectionScale = json_state["crossSectionScale"]
        if "projectionOrientation" in json_state:
            projectionOrientation = json_state["projectionOrientation"]
        else:
            default_orientation = [0, 0, 0, 1]
            projectionOrientation = default_orientation
            json_state["projectionOrientation"] = default_orientation
        projectionScale = json_state["projectionScale"]
        if add_mouse:
            curr_image = self.get_screenshot(image_path, resize=resize, mouse_x=self.mouse_x, mouse_y=self.mouse_y, fast=fast)
        else:
            curr_image = self.get_screenshot(image_path, resize=resize, fast=fast)
        if euler_angles:
            projectionOrientationEuler = quaternion_to_euler(projectionOrientation)
            pos_state = [position, crossSectionScale, projectionOrientationEuler, projectionScale]
        else:
            pos_state = [position, crossSectionScale, projectionOrientation, projectionScale]
        return (pos_state, curr_image), json_state


"""
To define:

step(self, action) → Takes an action and returns:
                        observation (new state)
                        reward (immediate reward)
                        done (whether the episode is over)
                        info (optional metadata)
State & Action Space
    observation_space(self) → Defines the shape and range of observations.
    action_space(self) → Defines the valid action set.
Seeding (for reproducibility)
    seed(self, seed=None) → Sets a random seed.
Reward Calculation (if separate)
    compute_reward(self, state, action) → Computes the reward based on state and action.
"""


# DEFINE WHAT THE STATE IS
# DEFINE WHAT THE ACTION SPACE IS
# DEFINE WHAT THE REWARD IS
# DEFINE WHAT THE DONE IS
# DEFINE WHAT THE INFO IS
# DEFINE WHAT THE RENDER IS
# DEFINE WHAT THE CLOSE IS

if __name__ == "__main__":
    env = Environment()
    env.start_session()

    
    for i in range(100):
        (pos_state, curr_image), json_state = env.prepare_state(image_path=None, euler_angles=True, resize=False, add_mouse=False, fast=True) # time is about 0.05 seconds
        # --> action_vector = model.predict(pos_state, curr_image)
        # For example purpose, lets use a random action
        action_vector = [
            0, 0, 0,  # left, right, double click booleans
            100, 100,  # x, y
            0, 0, 0,  # no modifier keys
            1,  # no JSON change
            10, 0, 0,  # position change
            0,  # cross-section scaling
            0.2, 0, 0,  # orientation change in Euler angles, which is better for a model to learn or a human to understand
            2000  # projection scaling (log-scale in neuroglancer)
            ]
        
        env.apply_actions(action_vector, json_state=json_state, euler_angles=True)


# This is an image in NGL.

# The action space is 
#             (
#             left_click, right_click, double_click,  # 3 booleans
#             x, y,                                  # 2 floats for mouse position
#             key_Shift, key_Ctrl, key_Alt,          # 3 booleans for keys
#             json_change,                           # 1 boolean for JSON change
#             delta_position_x, delta_position_y, delta_position_z,  # 3 floats
#             delta_crossSectionScale,               # 1 float
#             delta_projectionOrientation_e1, delta_projectionOrientation_e2, delta_projectionOrientation_e3,  # 3 floats
#             delta_projectionScale                  # 1 float
#             )
# Return the action that will click on the soma./ highest.
# + 
# Image
# """
# ChatGPT
# Claude