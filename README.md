A work in progress.

Quick-note-taking web app. Text or media (audio, image, video). With Google Login.

## Docker Compose Database Configuration
The database file is stored in a volume that can be configured via the `DB_VOLUME_PATH` environment variable:
- Default location: `./data/tilas.db` relative to docker-compose.yml
- To use a custom location: `export DB_VOLUME_PATH=/path/to/your/database/folder`