BEGIN;
SELECT setval(pg_get_serial_sequence('"TDMS_account"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "TDMS_account";
SELECT setval(pg_get_serial_sequence('"TDMS_location"','location_id'), coalesce(max("location_id"), 1), max("location_id") IS NOT null) FROM "TDMS_location";
SELECT setval(pg_get_serial_sequence('"TDMS_bookmark"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "TDMS_bookmark";
SELECT setval(pg_get_serial_sequence('"TDMS_note"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "TDMS_note";
COMMIT;
