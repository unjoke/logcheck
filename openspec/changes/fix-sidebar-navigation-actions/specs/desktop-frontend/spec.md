## ADDED Requirements

### Requirement: Sidebar navigation actions are meaningful
The desktop front end SHALL ensure every left sidebar button either switches the visible workspace section to matching content or triggers the existing local function named by the button.

#### Scenario: Switch to overview section
- **WHEN** the user clicks the Overview sidebar button
- **THEN** the main workspace displays the analysis overview section

#### Scenario: Open local log source selection
- **WHEN** the user clicks the Log Sources sidebar button
- **THEN** the desktop UI invokes the local log file selection workflow

#### Scenario: Switch to rule section
- **WHEN** the user clicks the Detection Rules sidebar button
- **THEN** the main workspace displays detection rule status content

#### Scenario: Switch to suspicious source section
- **WHEN** the user clicks the Suspicious Sources sidebar button
- **THEN** the main workspace displays suspicious source content derived from the latest local analysis when available

#### Scenario: Trigger report export
- **WHEN** the user clicks the Export Report sidebar button
- **THEN** the desktop UI invokes the existing local report export workflow

#### Scenario: Switch to course demo section
- **WHEN** the user clicks the Course Demo sidebar button
- **THEN** the main workspace displays local course demonstration content

### Requirement: Sidebar buttons provide click feedback
The desktop front end SHALL provide visible hover, pressed, and selected states for left sidebar buttons.

#### Scenario: Highlight selected sidebar section
- **WHEN** a sidebar section is selected
- **THEN** that button is visually distinguished from unselected sidebar buttons

#### Scenario: Show tactile button state
- **WHEN** the user hovers over or presses a sidebar button
- **THEN** the button appearance changes to communicate that it is clickable
