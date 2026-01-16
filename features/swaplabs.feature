@playwrighttests
Feature: Swag Labs Login and Product Access

  Scenario: Successful standard user login
    Given a new Playwright client is initialized for Swag Labs
    When the user logs in with a valid standard username and password
    Then the user should be on the inventory page
    And the page title should contain "Swag2 Labs" for swaplabs

  Scenario: Failed login attempt (Testing WebElement Failure Capture)
    Given a new Playwright client is initialized for Swag Labs
    When the user attempts to log in with an invalid username and password
    Then the login error message should be visible on the page