from django.test import TestCase,LiveServerTestCase
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
import time
# Create your tests here.
# Generated by Selenium IDE

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options





# Generated by Selenium IDE

class TestTestNavbarButtons(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)

    def tearDown(self):
        self.driver.quit()

    def test_testNavbarButtons(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)


        self.driver.find_element(By.LINK_TEXT, "My Watchlist").click()
        time.sleep(2)

        self.assertIn("/watchlist", self.driver.current_url)

        self.driver.find_element(By.LINK_TEXT, "Discover").click()
        time.sleep(2)

        self.driver.find_element(By.LINK_TEXT, "My Watchlist").click()
        time.sleep(2)

        self.assertIn("/watchlist", self.driver.current_url)

        self.driver.find_element(By.LINK_TEXT, "FlickFinder").click()
        time.sleep(2)

# Generated by Selenium IDE


class TestTestSwipe(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)

    def tearDown(self):
        self.driver.quit()

    def test_testSwipe(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)

        time.sleep(2)
        self.driver.find_element(By.CSS_SELECTOR, "body").click()
        time.sleep(2)

# Generated by Selenium IDE

class TestTestSkip(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)

    def tearDown(self):
        self.driver.quit()

    def test_testSkip(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "authForm").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)


        button_selector = '.action-btn:nth-child(1)'

        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)

        feedback = self.wait.until(
            EC.visibility_of_element_located((By.ID, "feedback-overlay"))
        )

        # Assert that the feedback text is correct and visible
        self.assertIn("Skipped", feedback.text.strip())
        self.assertTrue(feedback.is_displayed())
        time.sleep(2)

# Generated by Selenium IDE

class TestTestBlocked(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)

    def tearDown(self):
        self.driver.quit()

    def test_testBlocked(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "authForm").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)

        button_selector = '.action-btn:nth-child(2)'

        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)

        feedback = self.wait.until(
            EC.visibility_of_element_located((By.ID, "feedback-overlay"))
        )

        # Assert that the feedback text is correct and visible
        self.assertIn("Blocked", feedback.text.strip())
        self.assertTrue(feedback.is_displayed())
        time.sleep(2)

# Generated by Selenium IDE

class TestTestHeart(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)

    def tearDown(self):
        self.driver.quit()

    def test_testHeart(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)

        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)

        button_selector = '.action-btn:nth-child(3)'

        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)

        feedback = self.wait.until(
            EC.visibility_of_element_located((By.ID, "feedback-overlay"))
        )

        # Assert that the feedback text is correct and visible
        self.assertIn("Favorited", feedback.text.strip())
        self.assertTrue(feedback.is_displayed())
        time.sleep(2)



# Generated by Selenium IDE

class TestTestWishlist(TestCase):
    def setUp(self):
        options = webdriver.FirefoxOptions()
        options.headless = False
        self.driver = webdriver.Firefox(options=options)

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)
    def tearDown(self):
        self.driver.quit()

    def test_testWishlist(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)

        # Click the wishlist button
        button_selector = '.action-btn:nth-child(4)'
        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)

        feedback = self.wait.until(
            EC.visibility_of_element_located((By.ID, "feedback-overlay"))
        )

        # Assert that the feedback text is correct and visible
        self.assertIn("Added to Watchlist", feedback.text.strip())
        self.assertTrue(feedback.is_displayed())




class TestTestDetails(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)
    def tearDown(self):
        self.driver.quit()

    def test_testDetails(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)

        button_selector = '.movie-poster'

        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)
        time.sleep(2)

        detail_header = self.wait.until(EC.presence_of_element_located((By.XPATH, "//h4[contains(., 'Overview')]")))
        self.assertTrue(detail_header.is_displayed())

class TestMovieSearch(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)
    def tearDown(self):
        self.driver.quit()

    def test_movieSearch(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "authForm").click()
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)

        self.driver.find_element(By.NAME, "query").click()
        time.sleep(2)
        self.driver.find_element(By.NAME, "query").send_keys("Chitty Chitty Bang Bang")
        time.sleep(2)

        self.driver.find_element(By.CSS_SELECTOR, ".fa-search").click()
        time.sleep(2)

        self.assertIn("Chitty Chitty Bang Bang", self.driver.page_source)




# Generated by Selenium IDE

class TestTestMovieDetailOptions(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)
    def tearDown(self):
        self.driver.quit()

    def test_testMovieDetailOptions(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()
        self.driver.find_element(By.CSS_SELECTOR, ".movie-poster").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)

        button_selector = '.btn-outline-danger'

        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)
        time.sleep(2)

        button_selector = ".btn-outline-warning"

        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)
        time.sleep(2)

        button_selector = ".btn-outline-success"

        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)
        time.sleep(2)

# Generated by Selenium IDE

class TestTestFilter(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)
    def tearDown(self):
        self.driver.quit()

    def test_testFilter(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)

        time.sleep(2)

        element = self.driver.find_element(By.CSS_SELECTOR, ".btn-outline-primary")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()

        time.sleep(2)

        self.driver.find_element(By.CSS_SELECTOR, ".btn-outline-primary").click()
        element = self.driver.find_element(By.CSS_SELECTOR, "body")
        actions = ActionChains(self.driver)
        actions.move_to_element(element).perform()

        time.sleep(2)

        self.driver.find_element(By.ID, "genre_28").click()
        time.sleep(2)

        self.driver.find_element(By.ID, "genre_99").click()
        time.sleep(2)

        self.driver.find_element(By.ID, "id_min_release_year").click()
        time.sleep(2)

        self.driver.find_element(By.ID, "id_min_release_year").send_keys("2000")
        time.sleep(2)

        self.driver.find_element(By.ID, "id_max_release_year").click()
        time.sleep(2)

        self.driver.find_element(By.ID, "id_max_release_year").send_keys("2020")
        time.sleep(2)

        self.driver.find_element(By.ID, "id_min_rating").click()
        time.sleep(2)

        self.driver.find_element(By.ID, "id_min_rating").send_keys("5")
        time.sleep(2)

        self.driver.find_element(By.ID, "saveFilters").click()
        time.sleep(2)

        self.driver.find_element(By.CSS_SELECTOR, ".btn-outline-primary").click()
        time.sleep(2)

        self.driver.find_element(By.ID, "clearFilters").click()
        time.sleep(2)





# Generated by Selenium IDE

class TestTestRemove(TestCase):
    def setUp(self):
        self.driver = webdriver.Firefox()
        self.vars = {}

        self.wait = WebDriverWait(self.driver, 15)
        self.driver.set_window_size(1440, 900)

    def tearDown(self):
        self.driver.quit()

    def test_testRemove(self):
        self.driver.get("http://54.209.182.216/")
        self.driver.set_window_size(1440, 900)
        self.driver.find_element(By.LINK_TEXT, "Login").click()
        self.driver.find_element(By.ID, "username").click()
        self.driver.find_element(By.ID, "username").send_keys("willt")
        self.driver.find_element(By.ID, "password").click()
        self.driver.find_element(By.ID, "password").send_keys("PasswordlyPass#21!")
        self.driver.find_element(By.CSS_SELECTOR, ".btn-primary").click()
        self.driver.find_element(By.LINK_TEXT, "My Watchlist").click()

        logout_button = self.wait.until(EC.presence_of_element_located((By.XPATH, "//button[contains(.,'Log Out')]")))
        self.assertTrue(logout_button.is_displayed())
        time.sleep(2)


        button_selector = '.col-xl-3:nth-child(1) .btn:nth-child(1)'

        button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, button_selector)))

        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
        time.sleep(2)
        self.driver.execute_script("arguments[0].click();", button)
        time.sleep(2)






