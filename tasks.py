from app import celery, llm


@celery.task
def create_index_task():
    llm.create_index()


__all__ = ["create_index_task"]