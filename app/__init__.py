from fastapi import FastAPI


def create_app() -> FastAPI:
    from app.routes import router

    application = FastAPI(title="Anthropic RAG API")
    application.include_router(router)
    return application


app = create_app()

