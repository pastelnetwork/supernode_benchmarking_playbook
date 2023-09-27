from web_app.app.database.data_models import RawBenchmarkSubscores, OverallNormalizedScore
from web_app.app.logger_config import setup_logger
import pandas as pd
import plotly.express as px
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from decouple import config

logger = setup_logger()
MAX_DATA_POINTS_FOR_CHART = config("MAX_DATA_POINTS_FOR_CHART", cast=int) 

async def generate_benchmark_charts(db: Session):
    logger.info("Generating benchmark charts.")
    # Query for raw benchmark subscores
    raw_stats = db.query(RawBenchmarkSubscores).order_by(RawBenchmarkSubscores.datetime.desc()).limit(MAX_DATA_POINTS_FOR_CHART).all()
    raw_stats_dict = [{column.name: getattr(s, column.name) for column in RawBenchmarkSubscores.__table__.columns} for s in raw_stats]
    raw_df = pd.DataFrame(raw_stats_dict)
    raw_df['datetime'] = pd.to_datetime(raw_df['datetime'])
    subscore_fig = px.line(raw_df, x='datetime', y=['cpu_speed_test__events_per_second', 'fileio_test__reads_per_second', 'memory_speed_test__MiB_transferred', 'mutex_test__avg_latency','threads_test__avg_latency'], color='variable',
                    labels={'value': 'Metric Value', 'datetime': 'Datetime', 'variable': 'Benchmark Test'}, title='Raw Benchmark Metrics Over Time', markers=True)
    subscore_fig.update_traces(hoverinfo="name+ip+datetime+metric")
    
    # Query for overall normalized scores
    overall_stats = db.query(OverallNormalizedScore).order_by(OverallNormalizedScore.datetime.desc()).limit(MAX_DATA_POINTS_FOR_CHART).all()
    overall_stats_dict = [{column.name: getattr(s, column.name) for column in OverallNormalizedScore.__table__.columns} for s in overall_stats]
    overall_df = pd.DataFrame(overall_stats_dict)
    overall_df['datetime'] = pd.to_datetime(overall_df['datetime'])
    overall_fig = px.line(overall_df, x='datetime', y='overall_score', color='hostname',
                        labels={'overall_score': 'Overall Score', 'datetime': 'Datetime', 'hostname': 'Machine'}, title='Overall Normalized Scores Over Time', markers=True)
    overall_fig.update_traces(hoverinfo="name+ip+datetime+score")
    logger.info("Benchmark charts generated successfully.")        
    return HTMLResponse(content=f'<div>{subscore_fig.to_html(full_html=False)}</div><div>{overall_fig.to_html(full_html=False)}</div>')
