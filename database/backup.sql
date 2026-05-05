--
-- PostgreSQL database dump
--

\restrict Np9nbOKBJJzhGswBz6lbumN4DVpSgvU6XzyUoNrGVybkU59qUQNYyjClQYMVHcO

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

-- Started on 2026-05-01 13:10:18

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

DROP DATABASE aires_ucc_monteria;
--
-- TOC entry 5164 (class 1262 OID 16669)
-- Name: aires_ucc_monteria; Type: DATABASE; Schema: -; Owner: postgres
--

CREATE DATABASE aires_ucc_monteria WITH TEMPLATE = template0 ENCODING = 'UTF8' LOCALE_PROVIDER = libc LOCALE = 'Spanish_Colombia.1252';


ALTER DATABASE aires_ucc_monteria OWNER TO postgres;

\unrestrict Np9nbOKBJJzhGswBz6lbumN4DVpSgvU6XzyUoNrGVybkU59qUQNYyjClQYMVHcO
\connect aires_ucc_monteria
\restrict Np9nbOKBJJzhGswBz6lbumN4DVpSgvU6XzyUoNrGVybkU59qUQNYyjClQYMVHcO

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 245 (class 1259 OID 16911)
-- Name: auditoria; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.auditoria (
    id integer NOT NULL,
    tabla_afectada character varying(60) NOT NULL,
    registro_id integer NOT NULL,
    campo character varying(60) NOT NULL,
    valor_anterior text,
    valor_nuevo text,
    encargado_id integer,
    fecha_cambio timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE gestion_aires_ucc.auditoria OWNER TO postgres;

--
-- TOC entry 244 (class 1259 OID 16910)
-- Name: auditoria_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.auditoria_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.auditoria_id_seq OWNER TO postgres;

--
-- TOC entry 5165 (class 0 OID 0)
-- Dependencies: 244
-- Name: auditoria_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.auditoria_id_seq OWNED BY gestion_aires_ucc.auditoria.id;


--
-- TOC entry 231 (class 1259 OID 16730)
-- Name: bloques; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.bloques (
    id integer NOT NULL,
    codigo_bloque character varying(15) NOT NULL,
    nombre_bloque character varying(65) NOT NULL
);


ALTER TABLE gestion_aires_ucc.bloques OWNER TO postgres;

--
-- TOC entry 230 (class 1259 OID 16729)
-- Name: bloques_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.bloques_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.bloques_id_seq OWNER TO postgres;

--
-- TOC entry 5166 (class 0 OID 0)
-- Dependencies: 230
-- Name: bloques_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.bloques_id_seq OWNED BY gestion_aires_ucc.bloques.id;


--
-- TOC entry 241 (class 1259 OID 16846)
-- Name: componentes_usados; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.componentes_usados (
    id integer NOT NULL,
    cantidad numeric(3,1) NOT NULL,
    precio_unitario numeric(10,2),
    mantenimiento_realizado_id integer NOT NULL,
    repuesto_utilizado_id integer NOT NULL
);


ALTER TABLE gestion_aires_ucc.componentes_usados OWNER TO postgres;

--
-- TOC entry 240 (class 1259 OID 16845)
-- Name: componentes_usados_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.componentes_usados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.componentes_usados_id_seq OWNER TO postgres;

--
-- TOC entry 5167 (class 0 OID 0)
-- Dependencies: 240
-- Name: componentes_usados_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.componentes_usados_id_seq OWNED BY gestion_aires_ucc.componentes_usados.id;


--
-- TOC entry 237 (class 1259 OID 16802)
-- Name: encargados; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.encargados (
    id integer NOT NULL,
    codigo_universitario integer NOT NULL,
    nombre character varying(30) NOT NULL,
    apellido character varying(30) NOT NULL,
    tipo_rol character varying(50) NOT NULL,
    telefono character varying(12) NOT NULL,
    correo_institucional character varying(50),
    CONSTRAINT chk_encargados_tipo_rol CHECK (((tipo_rol)::text = ANY ((ARRAY['Tecnico interno'::character varying, 'Supervisor'::character varying, 'Administrador'::character varying, 'Contratista'::character varying, 'Solo lectura'::character varying])::text[])))
);


ALTER TABLE gestion_aires_ucc.encargados OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 16801)
-- Name: encargados_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.encargados_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.encargados_id_seq OWNER TO postgres;

--
-- TOC entry 5168 (class 0 OID 0)
-- Dependencies: 236
-- Name: encargados_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.encargados_id_seq OWNED BY gestion_aires_ucc.encargados.id;


--
-- TOC entry 235 (class 1259 OID 16771)
-- Name: equipos; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.equipos (
    id integer NOT NULL,
    codigo_activo character varying(50) CONSTRAINT equipos_serial_not_null NOT NULL,
    modelo character varying(50),
    capacidad_btu integer NOT NULL,
    fecha_instalacion date,
    estado character varying(20) DEFAULT 'Operativo'::character varying,
    marca_id integer NOT NULL,
    tipo_equipo_id integer NOT NULL,
    espacio_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_estado_equipos CHECK (((estado)::text = ANY ((ARRAY['Operativo'::character varying, 'En reparacion'::character varying, 'Inactivo'::character varying, 'Dado de baja'::character varying])::text[])))
);


ALTER TABLE gestion_aires_ucc.equipos OWNER TO postgres;

--
-- TOC entry 234 (class 1259 OID 16770)
-- Name: equipos_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.equipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.equipos_id_seq OWNER TO postgres;

--
-- TOC entry 5169 (class 0 OID 0)
-- Dependencies: 234
-- Name: equipos_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.equipos_id_seq OWNED BY gestion_aires_ucc.equipos.id;


--
-- TOC entry 233 (class 1259 OID 16749)
-- Name: espacios; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.espacios (
    id integer NOT NULL,
    codigo_espacio character varying(20) NOT NULL,
    nombre character varying(65) NOT NULL,
    piso integer,
    bloque_id integer NOT NULL,
    tipo_espacio_id integer NOT NULL
);


ALTER TABLE gestion_aires_ucc.espacios OWNER TO postgres;

--
-- TOC entry 232 (class 1259 OID 16748)
-- Name: espacios_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.espacios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.espacios_id_seq OWNER TO postgres;

--
-- TOC entry 5170 (class 0 OID 0)
-- Dependencies: 232
-- Name: espacios_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.espacios_id_seq OWNED BY gestion_aires_ucc.espacios.id;


--
-- TOC entry 239 (class 1259 OID 16817)
-- Name: mantenimientos; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.mantenimientos (
    id integer NOT NULL,
    fecha_mantenimiento date NOT NULL,
    detalle_mantenimiento text,
    equipo_id integer NOT NULL,
    encargado_id integer NOT NULL,
    tipo_mantenimiento_id integer CONSTRAINT mantenimientos_tipo_trabajo_not_null NOT NULL,
    registrado_por integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE gestion_aires_ucc.mantenimientos OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 16816)
-- Name: mantenimientos_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.mantenimientos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.mantenimientos_id_seq OWNER TO postgres;

--
-- TOC entry 5171 (class 0 OID 0)
-- Dependencies: 238
-- Name: mantenimientos_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.mantenimientos_id_seq OWNED BY gestion_aires_ucc.mantenimientos.id;


--
-- TOC entry 221 (class 1259 OID 16672)
-- Name: marcas; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.marcas (
    id integer NOT NULL,
    nombre character varying(20) NOT NULL
);


ALTER TABLE gestion_aires_ucc.marcas OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16671)
-- Name: marcas_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.marcas_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.marcas_id_seq OWNER TO postgres;

--
-- TOC entry 5172 (class 0 OID 0)
-- Dependencies: 220
-- Name: marcas_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.marcas_id_seq OWNED BY gestion_aires_ucc.marcas.id;


--
-- TOC entry 243 (class 1259 OID 16881)
-- Name: programaciones; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.programaciones (
    id integer NOT NULL,
    fecha_programada date NOT NULL,
    equipo_id integer NOT NULL,
    encargado_id integer NOT NULL,
    tipo_mantenimiento_id integer NOT NULL,
    estado character varying(20) DEFAULT 'Pendiente'::character varying NOT NULL,
    mantenimiento_id integer,
    CONSTRAINT programaciones_estado_check CHECK (((estado)::text = ANY ((ARRAY['Pendiente'::character varying, 'Completado'::character varying, 'Cancelado'::character varying, 'Vencido'::character varying])::text[])))
);


ALTER TABLE gestion_aires_ucc.programaciones OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 16880)
-- Name: programaciones_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.programaciones_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.programaciones_id_seq OWNER TO postgres;

--
-- TOC entry 5173 (class 0 OID 0)
-- Dependencies: 242
-- Name: programaciones_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.programaciones_id_seq OWNED BY gestion_aires_ucc.programaciones.id;


--
-- TOC entry 229 (class 1259 OID 16717)
-- Name: tipos_componentes; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.tipos_componentes (
    id integer NOT NULL,
    nombre character varying(60) NOT NULL,
    unidad_medida character varying(35)
);


ALTER TABLE gestion_aires_ucc.tipos_componentes OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 16716)
-- Name: tipos_componentes_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.tipos_componentes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.tipos_componentes_id_seq OWNER TO postgres;

--
-- TOC entry 5174 (class 0 OID 0)
-- Dependencies: 228
-- Name: tipos_componentes_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.tipos_componentes_id_seq OWNED BY gestion_aires_ucc.tipos_componentes.id;


--
-- TOC entry 225 (class 1259 OID 16694)
-- Name: tipos_equipos; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.tipos_equipos (
    id integer NOT NULL,
    nombre character varying(30) NOT NULL
);


ALTER TABLE gestion_aires_ucc.tipos_equipos OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16693)
-- Name: tipos_equipos_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.tipos_equipos_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.tipos_equipos_id_seq OWNER TO postgres;

--
-- TOC entry 5175 (class 0 OID 0)
-- Dependencies: 224
-- Name: tipos_equipos_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.tipos_equipos_id_seq OWNED BY gestion_aires_ucc.tipos_equipos.id;


--
-- TOC entry 223 (class 1259 OID 16683)
-- Name: tipos_espacios; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.tipos_espacios (
    id integer NOT NULL,
    nombre character varying(50) NOT NULL
);


ALTER TABLE gestion_aires_ucc.tipos_espacios OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16682)
-- Name: tipos_espacios_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.tipos_espacios_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.tipos_espacios_id_seq OWNER TO postgres;

--
-- TOC entry 5176 (class 0 OID 0)
-- Dependencies: 222
-- Name: tipos_espacios_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.tipos_espacios_id_seq OWNED BY gestion_aires_ucc.tipos_espacios.id;


--
-- TOC entry 227 (class 1259 OID 16705)
-- Name: tipos_mantenimiento; Type: TABLE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE TABLE gestion_aires_ucc.tipos_mantenimiento (
    id integer NOT NULL,
    nombre character varying(30) NOT NULL,
    frecuencia_dias integer
);


ALTER TABLE gestion_aires_ucc.tipos_mantenimiento OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16704)
-- Name: tipos_mantenimiento_id_seq; Type: SEQUENCE; Schema: gestion_aires_ucc; Owner: postgres
--

CREATE SEQUENCE gestion_aires_ucc.tipos_mantenimiento_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE gestion_aires_ucc.tipos_mantenimiento_id_seq OWNER TO postgres;

--
-- TOC entry 5177 (class 0 OID 0)
-- Dependencies: 226
-- Name: tipos_mantenimiento_id_seq; Type: SEQUENCE OWNED BY; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER SEQUENCE gestion_aires_ucc.tipos_mantenimiento_id_seq OWNED BY gestion_aires_ucc.tipos_mantenimiento.id;


--
-- TOC entry 4921 (class 2604 OID 16914)
-- Name: auditoria id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.auditoria ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.auditoria_id_seq'::regclass);


--
-- TOC entry 4909 (class 2604 OID 16733)
-- Name: bloques id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.bloques ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.bloques_id_seq'::regclass);


--
-- TOC entry 4918 (class 2604 OID 16849)
-- Name: componentes_usados id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.componentes_usados ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.componentes_usados_id_seq'::regclass);


--
-- TOC entry 4915 (class 2604 OID 16805)
-- Name: encargados id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.encargados ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.encargados_id_seq'::regclass);


--
-- TOC entry 4911 (class 2604 OID 16774)
-- Name: equipos id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.equipos ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.equipos_id_seq'::regclass);


--
-- TOC entry 4910 (class 2604 OID 16752)
-- Name: espacios id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.espacios ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.espacios_id_seq'::regclass);


--
-- TOC entry 4916 (class 2604 OID 16820)
-- Name: mantenimientos id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.mantenimientos ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.mantenimientos_id_seq'::regclass);


--
-- TOC entry 4904 (class 2604 OID 16675)
-- Name: marcas id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.marcas ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.marcas_id_seq'::regclass);


--
-- TOC entry 4919 (class 2604 OID 16884)
-- Name: programaciones id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.programaciones ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.programaciones_id_seq'::regclass);


--
-- TOC entry 4908 (class 2604 OID 16720)
-- Name: tipos_componentes id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_componentes ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.tipos_componentes_id_seq'::regclass);


--
-- TOC entry 4906 (class 2604 OID 16697)
-- Name: tipos_equipos id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_equipos ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.tipos_equipos_id_seq'::regclass);


--
-- TOC entry 4905 (class 2604 OID 16686)
-- Name: tipos_espacios id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_espacios ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.tipos_espacios_id_seq'::regclass);


--
-- TOC entry 4907 (class 2604 OID 16708)
-- Name: tipos_mantenimiento id; Type: DEFAULT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_mantenimiento ALTER COLUMN id SET DEFAULT nextval('gestion_aires_ucc.tipos_mantenimiento_id_seq'::regclass);


--
-- TOC entry 5158 (class 0 OID 16911)
-- Dependencies: 245
-- Data for Name: auditoria; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--



--
-- TOC entry 5144 (class 0 OID 16730)
-- Dependencies: 231
-- Data for Name: bloques; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--



--
-- TOC entry 5154 (class 0 OID 16846)
-- Dependencies: 241
-- Data for Name: componentes_usados; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--



--
-- TOC entry 5150 (class 0 OID 16802)
-- Dependencies: 237
-- Data for Name: encargados; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--



--
-- TOC entry 5148 (class 0 OID 16771)
-- Dependencies: 235
-- Data for Name: equipos; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--



--
-- TOC entry 5146 (class 0 OID 16749)
-- Dependencies: 233
-- Data for Name: espacios; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--



--
-- TOC entry 5152 (class 0 OID 16817)
-- Dependencies: 239
-- Data for Name: mantenimientos; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--



--
-- TOC entry 5134 (class 0 OID 16672)
-- Dependencies: 221
-- Data for Name: marcas; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--

INSERT INTO gestion_aires_ucc.marcas VALUES (1, 'York');
INSERT INTO gestion_aires_ucc.marcas VALUES (2, 'Carrier');
INSERT INTO gestion_aires_ucc.marcas VALUES (3, 'LG');
INSERT INTO gestion_aires_ucc.marcas VALUES (4, 'Samsung');
INSERT INTO gestion_aires_ucc.marcas VALUES (5, 'Trane');


--
-- TOC entry 5156 (class 0 OID 16881)
-- Dependencies: 243
-- Data for Name: programaciones; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--



--
-- TOC entry 5142 (class 0 OID 16717)
-- Dependencies: 229
-- Data for Name: tipos_componentes; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--

INSERT INTO gestion_aires_ucc.tipos_componentes VALUES (1, 'Filtro', 'Unidades');
INSERT INTO gestion_aires_ucc.tipos_componentes VALUES (2, 'Gas Refrigerante', 'Libras');
INSERT INTO gestion_aires_ucc.tipos_componentes VALUES (3, 'Capacitor', 'Unidades');


--
-- TOC entry 5138 (class 0 OID 16694)
-- Dependencies: 225
-- Data for Name: tipos_equipos; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--

INSERT INTO gestion_aires_ucc.tipos_equipos VALUES (1, 'Mini-split');
INSERT INTO gestion_aires_ucc.tipos_equipos VALUES (2, 'Piso-techo');
INSERT INTO gestion_aires_ucc.tipos_equipos VALUES (3, 'Cassette');
INSERT INTO gestion_aires_ucc.tipos_equipos VALUES (4, 'Central');
INSERT INTO gestion_aires_ucc.tipos_equipos VALUES (5, 'Ventana');


--
-- TOC entry 5136 (class 0 OID 16683)
-- Dependencies: 223
-- Data for Name: tipos_espacios; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--

INSERT INTO gestion_aires_ucc.tipos_espacios VALUES (1, 'Aula');
INSERT INTO gestion_aires_ucc.tipos_espacios VALUES (2, 'Laboratorio');
INSERT INTO gestion_aires_ucc.tipos_espacios VALUES (3, 'Oficina administrativa');
INSERT INTO gestion_aires_ucc.tipos_espacios VALUES (4, 'Biblioteca');
INSERT INTO gestion_aires_ucc.tipos_espacios VALUES (5, 'Auditorio');
INSERT INTO gestion_aires_ucc.tipos_espacios VALUES (6, 'Sala de Profesores');


--
-- TOC entry 5140 (class 0 OID 16705)
-- Dependencies: 227
-- Data for Name: tipos_mantenimiento; Type: TABLE DATA; Schema: gestion_aires_ucc; Owner: postgres
--

INSERT INTO gestion_aires_ucc.tipos_mantenimiento VALUES (1, 'Preventivo', 90);
INSERT INTO gestion_aires_ucc.tipos_mantenimiento VALUES (2, 'Correctivo', 0);


--
-- TOC entry 5178 (class 0 OID 0)
-- Dependencies: 244
-- Name: auditoria_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.auditoria_id_seq', 1, false);


--
-- TOC entry 5179 (class 0 OID 0)
-- Dependencies: 230
-- Name: bloques_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.bloques_id_seq', 1, false);


--
-- TOC entry 5180 (class 0 OID 0)
-- Dependencies: 240
-- Name: componentes_usados_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.componentes_usados_id_seq', 1, false);


--
-- TOC entry 5181 (class 0 OID 0)
-- Dependencies: 236
-- Name: encargados_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.encargados_id_seq', 1, false);


--
-- TOC entry 5182 (class 0 OID 0)
-- Dependencies: 234
-- Name: equipos_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.equipos_id_seq', 1, false);


--
-- TOC entry 5183 (class 0 OID 0)
-- Dependencies: 232
-- Name: espacios_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.espacios_id_seq', 1, false);


--
-- TOC entry 5184 (class 0 OID 0)
-- Dependencies: 238
-- Name: mantenimientos_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.mantenimientos_id_seq', 1, false);


--
-- TOC entry 5185 (class 0 OID 0)
-- Dependencies: 220
-- Name: marcas_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.marcas_id_seq', 5, true);


--
-- TOC entry 5186 (class 0 OID 0)
-- Dependencies: 242
-- Name: programaciones_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.programaciones_id_seq', 1, false);


--
-- TOC entry 5187 (class 0 OID 0)
-- Dependencies: 228
-- Name: tipos_componentes_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.tipos_componentes_id_seq', 3, true);


--
-- TOC entry 5188 (class 0 OID 0)
-- Dependencies: 224
-- Name: tipos_equipos_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.tipos_equipos_id_seq', 5, true);


--
-- TOC entry 5189 (class 0 OID 0)
-- Dependencies: 222
-- Name: tipos_espacios_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.tipos_espacios_id_seq', 6, true);


--
-- TOC entry 5190 (class 0 OID 0)
-- Dependencies: 226
-- Name: tipos_mantenimiento_id_seq; Type: SEQUENCE SET; Schema: gestion_aires_ucc; Owner: postgres
--

SELECT pg_catalog.setval('gestion_aires_ucc.tipos_mantenimiento_id_seq', 2, true);


--
-- TOC entry 4969 (class 2606 OID 16924)
-- Name: auditoria auditoria_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.auditoria
    ADD CONSTRAINT auditoria_pkey PRIMARY KEY (id);


--
-- TOC entry 4947 (class 2606 OID 16740)
-- Name: bloques bloques_codigo_bloque_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.bloques
    ADD CONSTRAINT bloques_codigo_bloque_key UNIQUE (codigo_bloque);


--
-- TOC entry 4949 (class 2606 OID 16742)
-- Name: bloques bloques_nombre_bloque_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.bloques
    ADD CONSTRAINT bloques_nombre_bloque_key UNIQUE (nombre_bloque);


--
-- TOC entry 4951 (class 2606 OID 16738)
-- Name: bloques bloques_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.bloques
    ADD CONSTRAINT bloques_pkey PRIMARY KEY (id);


--
-- TOC entry 4965 (class 2606 OID 16855)
-- Name: componentes_usados componentes_usados_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.componentes_usados
    ADD CONSTRAINT componentes_usados_pkey PRIMARY KEY (id);


--
-- TOC entry 4959 (class 2606 OID 16815)
-- Name: encargados encargados_codigo_universitario_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.encargados
    ADD CONSTRAINT encargados_codigo_universitario_key UNIQUE (codigo_universitario);


--
-- TOC entry 4961 (class 2606 OID 16813)
-- Name: encargados encargados_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.encargados
    ADD CONSTRAINT encargados_pkey PRIMARY KEY (id);


--
-- TOC entry 4955 (class 2606 OID 16783)
-- Name: equipos equipos_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.equipos
    ADD CONSTRAINT equipos_pkey PRIMARY KEY (id);


--
-- TOC entry 4957 (class 2606 OID 16868)
-- Name: equipos equipos_serial_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.equipos
    ADD CONSTRAINT equipos_serial_key UNIQUE (codigo_activo);


--
-- TOC entry 4953 (class 2606 OID 16759)
-- Name: espacios espacios_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.espacios
    ADD CONSTRAINT espacios_pkey PRIMARY KEY (id);


--
-- TOC entry 4963 (class 2606 OID 16829)
-- Name: mantenimientos mantenimientos_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.mantenimientos
    ADD CONSTRAINT mantenimientos_pkey PRIMARY KEY (id);


--
-- TOC entry 4927 (class 2606 OID 16681)
-- Name: marcas marcas_nombre_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.marcas
    ADD CONSTRAINT marcas_nombre_key UNIQUE (nombre);


--
-- TOC entry 4929 (class 2606 OID 16679)
-- Name: marcas marcas_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.marcas
    ADD CONSTRAINT marcas_pkey PRIMARY KEY (id);


--
-- TOC entry 4967 (class 2606 OID 16894)
-- Name: programaciones programaciones_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.programaciones
    ADD CONSTRAINT programaciones_pkey PRIMARY KEY (id);


--
-- TOC entry 4943 (class 2606 OID 16726)
-- Name: tipos_componentes tipos_componentes_nombre_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_componentes
    ADD CONSTRAINT tipos_componentes_nombre_key UNIQUE (nombre);


--
-- TOC entry 4945 (class 2606 OID 16724)
-- Name: tipos_componentes tipos_componentes_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_componentes
    ADD CONSTRAINT tipos_componentes_pkey PRIMARY KEY (id);


--
-- TOC entry 4935 (class 2606 OID 16703)
-- Name: tipos_equipos tipos_equipos_nombre_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_equipos
    ADD CONSTRAINT tipos_equipos_nombre_key UNIQUE (nombre);


--
-- TOC entry 4937 (class 2606 OID 16701)
-- Name: tipos_equipos tipos_equipos_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_equipos
    ADD CONSTRAINT tipos_equipos_pkey PRIMARY KEY (id);


--
-- TOC entry 4931 (class 2606 OID 16692)
-- Name: tipos_espacios tipos_espacios_nombre_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_espacios
    ADD CONSTRAINT tipos_espacios_nombre_key UNIQUE (nombre);


--
-- TOC entry 4933 (class 2606 OID 16690)
-- Name: tipos_espacios tipos_espacios_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_espacios
    ADD CONSTRAINT tipos_espacios_pkey PRIMARY KEY (id);


--
-- TOC entry 4939 (class 2606 OID 16715)
-- Name: tipos_mantenimiento tipos_mantenimiento_nombre_key; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_mantenimiento
    ADD CONSTRAINT tipos_mantenimiento_nombre_key UNIQUE (nombre);


--
-- TOC entry 4941 (class 2606 OID 16713)
-- Name: tipos_mantenimiento tipos_mantenimiento_pkey; Type: CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.tipos_mantenimiento
    ADD CONSTRAINT tipos_mantenimiento_pkey PRIMARY KEY (id);


--
-- TOC entry 4985 (class 2606 OID 16925)
-- Name: auditoria auditoria_encargado_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.auditoria
    ADD CONSTRAINT auditoria_encargado_id_fkey FOREIGN KEY (encargado_id) REFERENCES gestion_aires_ucc.encargados(id);


--
-- TOC entry 4979 (class 2606 OID 16856)
-- Name: componentes_usados componentes_usados_mantenimiento_realizado_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.componentes_usados
    ADD CONSTRAINT componentes_usados_mantenimiento_realizado_id_fkey FOREIGN KEY (mantenimiento_realizado_id) REFERENCES gestion_aires_ucc.mantenimientos(id);


--
-- TOC entry 4980 (class 2606 OID 16861)
-- Name: componentes_usados componentes_usados_repuesto_utilizado_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.componentes_usados
    ADD CONSTRAINT componentes_usados_repuesto_utilizado_id_fkey FOREIGN KEY (repuesto_utilizado_id) REFERENCES gestion_aires_ucc.tipos_componentes(id);


--
-- TOC entry 4972 (class 2606 OID 16796)
-- Name: equipos equipos_espacio_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.equipos
    ADD CONSTRAINT equipos_espacio_id_fkey FOREIGN KEY (espacio_id) REFERENCES gestion_aires_ucc.espacios(id);


--
-- TOC entry 4973 (class 2606 OID 16786)
-- Name: equipos equipos_marca_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.equipos
    ADD CONSTRAINT equipos_marca_id_fkey FOREIGN KEY (marca_id) REFERENCES gestion_aires_ucc.marcas(id);


--
-- TOC entry 4974 (class 2606 OID 16791)
-- Name: equipos equipos_tipo_equipo_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.equipos
    ADD CONSTRAINT equipos_tipo_equipo_id_fkey FOREIGN KEY (tipo_equipo_id) REFERENCES gestion_aires_ucc.tipos_equipos(id);


--
-- TOC entry 4970 (class 2606 OID 16760)
-- Name: espacios espacios_bloque_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.espacios
    ADD CONSTRAINT espacios_bloque_id_fkey FOREIGN KEY (bloque_id) REFERENCES gestion_aires_ucc.bloques(id);


--
-- TOC entry 4971 (class 2606 OID 16765)
-- Name: espacios espacios_tipo_espacio_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.espacios
    ADD CONSTRAINT espacios_tipo_espacio_id_fkey FOREIGN KEY (tipo_espacio_id) REFERENCES gestion_aires_ucc.tipos_espacios(id);


--
-- TOC entry 4975 (class 2606 OID 16835)
-- Name: mantenimientos mantenimientos_encargado_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.mantenimientos
    ADD CONSTRAINT mantenimientos_encargado_id_fkey FOREIGN KEY (encargado_id) REFERENCES gestion_aires_ucc.encargados(id);


--
-- TOC entry 4976 (class 2606 OID 16830)
-- Name: mantenimientos mantenimientos_equipo_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.mantenimientos
    ADD CONSTRAINT mantenimientos_equipo_id_fkey FOREIGN KEY (equipo_id) REFERENCES gestion_aires_ucc.equipos(id);


--
-- TOC entry 4977 (class 2606 OID 16873)
-- Name: mantenimientos mantenimientos_registrado_por_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.mantenimientos
    ADD CONSTRAINT mantenimientos_registrado_por_fkey FOREIGN KEY (registrado_por) REFERENCES gestion_aires_ucc.encargados(id);


--
-- TOC entry 4978 (class 2606 OID 16840)
-- Name: mantenimientos mantenimientos_tipo_trabajo_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.mantenimientos
    ADD CONSTRAINT mantenimientos_tipo_trabajo_fkey FOREIGN KEY (tipo_mantenimiento_id) REFERENCES gestion_aires_ucc.tipos_mantenimiento(id);


--
-- TOC entry 4981 (class 2606 OID 16900)
-- Name: programaciones programaciones_encargado_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.programaciones
    ADD CONSTRAINT programaciones_encargado_id_fkey FOREIGN KEY (encargado_id) REFERENCES gestion_aires_ucc.encargados(id);


--
-- TOC entry 4982 (class 2606 OID 16895)
-- Name: programaciones programaciones_equipo_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.programaciones
    ADD CONSTRAINT programaciones_equipo_id_fkey FOREIGN KEY (equipo_id) REFERENCES gestion_aires_ucc.equipos(id);


--
-- TOC entry 4983 (class 2606 OID 16930)
-- Name: programaciones programaciones_mantenimiento_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.programaciones
    ADD CONSTRAINT programaciones_mantenimiento_id_fkey FOREIGN KEY (mantenimiento_id) REFERENCES gestion_aires_ucc.mantenimientos(id);


--
-- TOC entry 4984 (class 2606 OID 16905)
-- Name: programaciones programaciones_tipo_mantenimiento_id_fkey; Type: FK CONSTRAINT; Schema: gestion_aires_ucc; Owner: postgres
--

ALTER TABLE ONLY gestion_aires_ucc.programaciones
    ADD CONSTRAINT programaciones_tipo_mantenimiento_id_fkey FOREIGN KEY (tipo_mantenimiento_id) REFERENCES gestion_aires_ucc.tipos_mantenimiento(id);


-- Completed on 2026-05-01 13:10:19

--
-- PostgreSQL database dump complete
--

\unrestrict Np9nbOKBJJzhGswBz6lbumN4DVpSgvU6XzyUoNrGVybkU59qUQNYyjClQYMVHcO

