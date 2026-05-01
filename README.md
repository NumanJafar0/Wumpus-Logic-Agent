# Dynamic Wumpus Logic Agent

A web-based Artificial Intelligence project demonstrating a Knowledge-Based Agent navigating a Wumpus World-style environment. The agent uses Propositional Logic and an automated Resolution Refutation Inference Engine to deduce safe paths dynamically.

Built with a **Python (Flask)** backend strictly handling all logic, state, and pathfinding, and a **Vanilla JS/HTML/CSS** frontend acting as a reactive UI.

## Features

* **Dynamic Environment Generation:** User-defined grid sizes ($M \times N$) with randomly distributed hazards (Pits and a Wumpus) at the start of every episode.
* **Propositional Logic Knowledge Base (KB):** The agent automatically translates physical percepts (Breeze, Stench) into Conjunctive Normal Form (CNF) rules.
* **Resolution Refutation Engine:** A custom Python inference engine that utilizes Proof by Contradiction and a Set of Support strategy to mathematically prove if an adjacent cell is safe or dangerous.
* **Dynamic Pathfinding:** Navigates via Depth-First Search (DFS) backtracking, moving strictly based on proven facts rather than probabilities.
* **Real-Time Visualization:** A responsive Web UI that updates instantly, color-coding cells as Safe (Green), Unknown (Gray), or Confirmed Danger (Red), alongside a live metrics dashboard.

## Project Structure

To run the application correctly, your files must be organized exactly like this:
```text
wumpus_project/
│
├── app.py                 # The Python Flask server and AI Logic Engine
└── templates/
    └── index.html         # The Frontend UI (HTML/CSS/JS)
