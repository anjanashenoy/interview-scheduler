from sqlalchemy import create_engine

external_engines = {
    'Northwestern University': create_engine(
        'postgresql://avnadmin:AVNS_Tyb3PrX9Do9pPiuo7kT@external-db-interview-scheduler.d.aivencloud.com:14977/defaultdb?sslmode=require'
    ),
    'University of Maryland': create_engine(
        'postgresql://avnadmin:AVNS_8QMfLX2AzoLwvOIHSkb@pg-23fc6f84-umd-external.h.aivencloud.com:22047/defaultdb?sslmode=require'
    ),
}
