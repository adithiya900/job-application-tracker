from celery_app import celery


@celery.task
def test_background_task():
    return "Background task executed successfully"