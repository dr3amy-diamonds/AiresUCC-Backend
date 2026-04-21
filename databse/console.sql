ALTER TABLE mantenimientos
RENAME COLUMN tipo_trabajo TO tipo_mantenimiento_id;

ALTER TABLE mantenimientos
ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;