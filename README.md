# Thunderbird Appointment

**Note: Thunderbird Appointment is a prototype still in active development, and is not production ready.**

Invite others to grab times on your calendar. Choose a date. Make appointments as easy as it gets.


## Feedback and Support

If you'd like to give feedback or need support, please see our [Topicbox](https://thunderbird.topicbox.com/groups/services).

## Get started

You can either build preconfigured docker containers (database, backend and frontend) or manually set up the application. A more detailed documentation can be found in the [docs folder](./docs/README.md).

### With Docker

```bash
git clone https://github.com/thunderbird/appointment
cp appointment/backend/.env.example appointment/backend/.env
cp appointment/frontend/.env.example appointment/frontend/.env
cd appointment
docker-compose up -d --build
```

* Frontend can be accessed via: <http://localhost:8080>
* Backend can be accessed via: <http://localhost:5173>
* OpenAPI docs can be accessed via: <http://localhost:5173/docs> or <http://localhost:5173/redoc>

A MySQL database will be accessible via `localhost:3306` with username and password set to: `tba`

To init database or run migrations, the backend offers a simple CLI interface:

```bash
run-command main update-db
```

### Manual Setup

Make sure to have the following prerequisites available:

```plain
Python >= 3.11
Node.js >= 16.0
```

Run application for development with hot reloading backend and frontend:

1. Get the application data

    ```bash
    git clone https://github.com/thunderbird/appointment
    ```

2. Install, configure and run python backend (it's recommended to do this in a virtual environment)

    ```bash
    cd appointment
    pip install .
    touch backend/src/appointment.db # when using sqlite
    cp backend/.env.example backend/.env # add your own configuration here
    uvicorn --factory appointment.main:server --host 0.0.0.0 --port 5000
    ```

    You can now access the backend at [localhost:5000](http://localhost:5000).

3. Install and run vue frontend in a second bash

    ```bash
    cd frontend
    npm install
    npm run dev
    ```

    You can now access the frontend at [localhost:8080](http://localhost:8080).

4. (optional) Run database migrations

    ```bash
    cd backend
    cp alembic.ini.example alembic.ini # add your own configuration here
    alembic init migrations # init migrations once
    alembic current # check database state
    alembic upgrade head # migrate to latest state
    alembic revision -m "create ... table" # create a new migration
    ```

## Testing

To run tests in the backend, simply install the package in editing mode:

```bash
cd backend && pip install -e .
```

After this you can run tests with:

```bash
cd backend && python -m pytest
```

To run tests in the frontend, do:

```bash
cd frontend && npm test
```

## Contributing

Contributions are very welcome. Please lint/format code before creating PRs.

### Backend

Backend is formatted using Ruff and Black.

```bash
pip install ruff
pip install black
```

Commands (from git root)

```bash
ruff backend
black backend
```

### Frontend

Frontend is formatted using ESlint with airbnb rules.

Commands (from /frontend)

```bash
npm run lint
npm run lint --fix
```

### Localization

This project uses [Fluent](https://projectfluent.org/) for localization. Files are located in their respective `l10n/<locale>/*.ftl`.
