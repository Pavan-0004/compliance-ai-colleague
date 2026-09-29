import uvicorn

from .config import get_config


def main():
    config = get_config()
    uvicorn.run("src.server:app", host=config.backend_host, port=config.backend_port, reload=False)


if __name__ == "__main__":
    main()
