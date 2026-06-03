# Agents in the Repository

## Edge Answer Agent
The Edge Answer Agent is responsible for producing final answers for tasks categorized as EDGE that do not require making git commits. Key functionalities include summarizing reports, explaining concepts, drafting messages, and extracting action items.

## Edge Coding Agent
The Edge Coding Agent generates precise file changes within the repository based on tasks requiring repository modifications. It provides concrete file contents in a structured format suitable for human application.

## GitHub Agent
The GitHub Agent manages repositories by cloning or updating them as necessary, keeping the repository context updated. It also summarizes repository contents, aiding in project understanding.

## Parser Agent
The Parser Agent converts user tasks into structured JSON format without executing code. It ensures that tasks are accurately represented in a structured, machine-readable way.

## Router Agent
The Router Agent evaluates incoming tasks across four dimensions: privacy sensitivity, security risk, task complexity, and latency sensitivity. It decides on the execution environment for tasks based on specified routing rules.