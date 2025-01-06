import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from exceptions import (
    CanNotLoginToRouterError,
    CanNotLogoutToRouterError,
    CanNotNavigateToProfileConfigError,
    CanNotSetNewPasswordError,
    EnableChannelError,
)

# Set to True to enable debugging
debugging = True

# Load the environment variables
load_dotenv()
ROUTER_USERNAME = os.getenv("ROUTER_USER_NAME")
ROUTER_PASSWORD = os.getenv("ROUTER_PASSWORD")
ROUTER_URL = os.getenv("ROUTER_URL")
NEW_PASSWORD = os.getenv("NEW_PASSWORD")
ENABLE_CHANNEL = os.getenv("ENABLE_CHANNEL").lower() in ("true", "1", "t")
try:
    ROUTER_CHANNEL = int(os.getenv("ROUTER_CHANNEL"))
except ValueError as e:
    print("Invalid value for ROUTER_CHANNEL in the environment variables ...!")
    sys.exit(1)

# Path to the ChromeDriver executable
script_directory = Path(__file__).resolve().parent
chrome_driver_path = script_directory / "chromedriver-win64" / "chromedriver.exe"

# Set up Chrome service and options
service = Service(chrome_driver_path)
chrome_options = Options()

# Set up Chrome options
if debugging:
    chrome_options.add_experimental_option("detach", True)
else:
    chrome_options.add_argument("--headless")


# login to the router
def login_to_router(driver: webdriver.Chrome):
    driver.get(ROUTER_URL)

    # Find the username and password fields
    username_field = driver.find_element(By.ID, "tf1_userName")
    password_field = driver.find_element(By.ID, "tf1_password")

    if username_field and password_field:
        username_field.send_keys(ROUTER_USERNAME)
        password_field.send_keys(ROUTER_PASSWORD)

    # Find the login button and click it
    login_button = driver.find_element(
        By.XPATH,
        "//button[@type='submit'][@class='loginBtn'][@title='Login'][@name='button.login.users.dashboard']",
    )

    if login_button:
        login_button.click()

    # Wait for the Dashboard to load and check if the login was successful
    try:
        WebDriverWait(driver, 5).until(
            EC.text_to_be_present_in_element((By.XPATH, "//body"), "Dashboard")
        )
        print("Login successful ...!")
    except TimeoutException as e:
        print("login failed ...!")
        raise CanNotLoginToRouterError(
            "function login_to_router() could not login to the router-dashboard."
        ) from e


# navigate to the profile configuration
class RouterNavigate:
    @staticmethod
    def to_dashboard(driver: webdriver.Chrome):
        # Find the Dashboard-menu and click it
        dashboard_element = driver.find_element(By.ID, "mainMenu1")
        if dashboard_element:
            dashboard_element.click()

    @staticmethod
    def to_wireless(driver: webdriver.Chrome):
        # Find the Network in menu and click it
        netwok_element = driver.find_element(By.ID, "mainMenu3")
        if netwok_element:
            netwok_element.click()

        # Find the Wireless optoin in the dropdown and click it
        wireless_element = driver.find_element(By.ID, "tf1_network_accessPoints")
        WebDriverWait(driver, 1).until(EC.element_to_be_clickable(wireless_element))
        if wireless_element:
            wireless_element.click()

    @staticmethod
    def to_profile_config(
        driver: webdriver.Chrome, actions: ActionChains, channel: int
    ):
        RouterNavigate.to_wireless(driver)
        # Find the Profiles and click it
        profiles_element = driver.find_element(
            By.XPATH, "//a[@onclick=\"gotoLinks('profiles.html')\"]"
        )
        if profiles_element:
            profiles_element.click()

        # Find the channel and right click on it
        channel_x = driver.find_element(By.XPATH, f'//tbody/tr[@id="{channel}"]/td[1]')
        if channel_x:
            actions.context_click(channel_x).perform()

        # Find the edit option and click it
        edit_element = driver.find_element(By.ID, "editMenu")
        if edit_element:
            edit_element.click()

        # Wait for the Wireless Profile Configuration page to load
        try:
            WebDriverWait(driver, 5).until(
                EC.text_to_be_present_in_element(
                    (By.XPATH, '//*[@id="tf1_dialog"]/div[1]/h1'),
                    "Wireless Profiles Configuration",
                )
                and EC.text_to_be_present_in_element(
                    (By.XPATH, '//*[@id="tf1_txtProfName_div"]/p'), f"Jio_{channel}"
                )
            )
            print(
                f"#. Navigated to the Wireless Profile Configuration page Jio_{channel} ..."
            )
        except TimeoutException as e:
            print(
                f"Navigation failed to the Wireless Profile Configuration page Jio{channel} ..."
            )
            raise CanNotNavigateToProfileConfigError(
                "function navigate_to_profie_config() could not navigate to the Wireless Profile Configuration page."
            ) from e


# set new password
def set_new_password(
    driver: webdriver.Chrome,
    actions: ActionChains,
    password: str = NEW_PASSWORD,
    channel: int = ROUTER_CHANNEL,
):
    RouterNavigate.to_profile_config(driver, actions, channel=channel)

    # Find the password field
    password_field = driver.find_element(By.ID, "tf1_txtWPAPasswd")
    if password_field:
        password_field.clear()
        password_field.send_keys(password)

    # Find the confirm password field
    confirm_password_field = driver.find_element(By.ID, "tf1_txtWPACnfPasswd")
    if confirm_password_field:
        confirm_password_field.clear()
        confirm_password_field.send_keys(password)

    # Find the save button and click it
    save_button = driver.find_element(By.XPATH, '//*[@id="tf1_dialog"]/div[3]/input[2]')
    if save_button:
        save_button.click()

    # Wait for the password to be updated and check if the operation was successful
    try:
        WebDriverWait(driver, 5).until(
            EC.text_to_be_present_in_element(
                (By.CSS_SELECTOR, "#main > div.msgInfo"), "Operation succeeded"
            )
        )
        print("Password updated successfully ...!")
    except TimeoutException as e:
        print("Password update failed ...!")
        raise CanNotSetNewPasswordError(
            "function set_new_password() could not update the password."
        ) from e


# enables channel
def enable_channel(
    driver: webdriver.Chrome,
    actions: ActionChains,
    channel: int = ROUTER_CHANNEL,
    enable: bool = ENABLE_CHANNEL,
):
    def common_op(id: str):
        # Right click on the channel
        actions.context_click(channel_x).perform()
        # Find the enable or disable option and click it
        enable_element = driver.find_element(By.ID, id)
        if enable_element:
            enable_element.click()

        # wait for the channel to be enebled and check if the operation was successful
        try:
            WebDriverWait(driver, 5).until(
                EC.text_to_be_present_in_element(
                    (By.CSS_SELECTOR, "#main > div.msgInfo"), "Operation succeeded"
                )
            )
            print(f"Channel {'Enabled' if enable else 'Disabled'} successfully ...!")
        except TimeoutException as e:
            print(f"Channel {'Enable' if enable else 'Disable'} failed ...!")
            raise EnableChannelError(
                f"function enable_channel() could not {'enable' if enable else 'disable'} the channel."
            ) from e

    RouterNavigate.to_wireless(driver)

    # Find the channel and get the status
    channel_x = driver.find_element(By.XPATH, f'//*[@id="{channel}"]/td[1]')
    if channel_x:
        is_enable = "enableIcon sorting_1" in channel_x.get_attribute("class")

    if enable and not is_enable:
        common_op("enableMenu")
    elif not enable and is_enable:
        common_op("disableMenu")
    else:
        RouterNavigate.to_dashboard(driver)


def logout_from_router(driver: webdriver.Chrome, actions: ActionChains):
    # find the logout dropdown label and content
    logout_dropdown_label = driver.find_element(By.ID, "lblLoggedinUser")
    logout_dropdown_content = driver.find_element(By.ID, "tf1_logoutAnchor")

    # move to the logout dropdown label and click the content
    if logout_dropdown_label and logout_dropdown_content:
        actions.move_to_element(logout_dropdown_label).perform()
        logout_dropdown_content.click()

    # find the logout ok button and click it
    logout_ok_button = driver.find_element(
        By.XPATH, '//*[@id="tf1_logOutContent"]/div/a[2]'
    )
    if logout_ok_button:
        logout_ok_button.click()

    # wait for the logout to be successful or check if the operation was successful
    try:
        WebDriverWait(driver, 5).until(
            EC.text_to_be_present_in_element(
                (By.XPATH, "/html/body/div[1]/div/div/div[2]/form/div/div[5]/button"),
                "Login",
            )
        )
        print("Logout successful ...!")
    except TimeoutException as e:
        print("Logout failed ...!")
        raise CanNotLogoutToRouterError(
            "function logout_from_router() could not logout from the router-dashboard."
        ) from e


def main():
    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=service, options=chrome_options)
    actions = ActionChains(driver)

    try:
        login_to_router(driver)
        set_new_password(driver, actions)
        enable_channel(driver, actions)
        logout_from_router(driver, actions)
    except WebDriverException as e:
        print(f"General Web Driver Exception Error: {e}")
    except CanNotLoginToRouterError as e:
        print(f"Can not Login to router Error: {e}")
    except CanNotNavigateToProfileConfigError as e:
        print(f"Can not Navigate to Profile Config Error: {e}")
    except CanNotSetNewPasswordError as e:
        print(f"Can not Set New Password Error: {e}")
    except EnableChannelError as e:
        print(f"Can not Enable Channel Error: {e}")
    except CanNotLogoutToRouterError as e:
        print(f"Can not Logout from router Error: {e}")
    finally:
        # Close the browser
        if not debugging:
            driver.quit()
            print("Browser closed ...!")


if __name__ == "__main__":
    main()
