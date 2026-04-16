# Backend

Backend code for the football match tracking and alert system.

## Structure

- `api/`
  Contains the internal API code used to return backend data to the frontend for rendering.

- `dummy/`
  Contains dummy data and test helpers used during development and testing.

- `events/`
  Contains event-related logic used by the backend.

- `routes/`
  Contains the Flask route handlers that define the backend's web endpoints.


- `db/database.py`
  Contains the logic for connecting to the database file.

- `app.py`
  Creates and configures the Flask application.

- `data_sync.py`
  Parses and processes data received from the API.

- `external_api.py`
  Handles communication with the external football data API.
