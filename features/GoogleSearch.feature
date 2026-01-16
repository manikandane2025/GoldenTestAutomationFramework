@playwrighttests1
Feature: Google Search Functionality
  As a user, I want to search for a query on Google
  So that I can find relevant information

  Scenario: User performs a search and verifies the results
    Given the user is on the Google search page
    When the user searches for "Playwright for automation"
    Then the page title should contain "Playwright"
    And the first search result should contain "Playwright"