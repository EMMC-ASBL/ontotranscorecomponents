import logging
from app.config.ontoRECSettings import OntoRECSetting

app_settings = OntoRECSetting()

FORMAT = ('%(asctime)-15s %(threadName)-15s %(levelname)-8s %(module)-15s:%(lineno)-8s %(message)s')
logging.basicConfig(format=FORMAT)
log = logging.getLogger(__name__)
log.setLevel(app_settings.LOG_LEVEL)