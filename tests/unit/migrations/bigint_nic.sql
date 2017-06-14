-- Dump taken just after migrating nic to BIGINT primary keyA
-- Commit hash: c200c9701a801ec3b34f749dce7f4f30dc2d1bd1
-- Extensions: Mock OBM, mock Switches
-- Generated with haas-admin db create

--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.7
-- Dumped by pg_dump version 9.5.7

SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: 
--



--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: 
--



SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);



--
-- Name: headnode; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE headnode (
    id integer NOT NULL,
    label character varying NOT NULL,
    project_id integer NOT NULL,
    dirty boolean NOT NULL,
    base_img character varying NOT NULL,
    uuid character varying NOT NULL
);



--
-- Name: headnode_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE headnode_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: headnode_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE headnode_id_seq OWNED BY headnode.id;


--
-- Name: hnic; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE hnic (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL,
    network_id integer
);



--
-- Name: hnic_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE hnic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: hnic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE hnic_id_seq OWNED BY hnic.id;


--
-- Name: metadata; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE metadata (
    id integer NOT NULL,
    label character varying NOT NULL,
    value character varying,
    owner_id integer NOT NULL
);



--
-- Name: metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE metadata_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE metadata_id_seq OWNED BY metadata.id;


--
-- Name: mock_obm; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE mock_obm (
    id integer NOT NULL,
    host character varying NOT NULL,
    "user" character varying NOT NULL,
    password character varying NOT NULL
);



--
-- Name: mock_switch; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE mock_switch (
    id integer NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL
);



--
-- Name: network; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE network (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer,
    allocated boolean,
    network_id character varying NOT NULL
);



--
-- Name: network_attachment; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE network_attachment (
    id integer NOT NULL,
    nic_id bigint NOT NULL,
    network_id integer NOT NULL,
    channel character varying NOT NULL
);



--
-- Name: network_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE network_attachment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: network_attachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE network_attachment_id_seq OWNED BY network_attachment.id;


--
-- Name: network_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE network_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: network_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE network_id_seq OWNED BY network.id;


--
-- Name: network_projects; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE network_projects (
    project_id integer,
    network_id integer
);



--
-- Name: networking_action; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE networking_action (
    id integer NOT NULL,
    type character varying NOT NULL,
    nic_id bigint NOT NULL,
    new_network_id integer,
    channel character varying NOT NULL
);



--
-- Name: networking_action_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE networking_action_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: networking_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE networking_action_id_seq OWNED BY networking_action.id;


--
-- Name: nic; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE nic (
    id bigint NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL,
    mac_addr character varying,
    port_id integer
);



--
-- Name: nic_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE nic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: nic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE nic_id_seq OWNED BY nic.id;


--
-- Name: node; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE node (
    id integer NOT NULL,
    label character varying NOT NULL,
    project_id integer,
    obm_id integer NOT NULL
);



--
-- Name: node_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE node_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: node_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE node_id_seq OWNED BY node.id;


--
-- Name: obm; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE obm (
    id integer NOT NULL,
    type character varying NOT NULL
);



--
-- Name: obm_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE obm_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: obm_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE obm_id_seq OWNED BY obm.id;


--
-- Name: port; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE port (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL
);



--
-- Name: port_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE port_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: port_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE port_id_seq OWNED BY port.id;


--
-- Name: project; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE project (
    id integer NOT NULL,
    label character varying NOT NULL
);



--
-- Name: project_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE project_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: project_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE project_id_seq OWNED BY project.id;


--
-- Name: switch; Type: TABLE; Schema: public; Owner: haas_dev
--

CREATE TABLE switch (
    id integer NOT NULL,
    label character varying NOT NULL,
    type character varying NOT NULL
);



--
-- Name: switch_id_seq; Type: SEQUENCE; Schema: public; Owner: haas_dev
--

CREATE SEQUENCE switch_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: switch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas_dev
--

ALTER SEQUENCE switch_id_seq OWNED BY switch.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY headnode ALTER COLUMN id SET DEFAULT nextval('headnode_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY hnic ALTER COLUMN id SET DEFAULT nextval('hnic_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY metadata ALTER COLUMN id SET DEFAULT nextval('metadata_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network ALTER COLUMN id SET DEFAULT nextval('network_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network_attachment ALTER COLUMN id SET DEFAULT nextval('network_attachment_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY networking_action ALTER COLUMN id SET DEFAULT nextval('networking_action_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY nic ALTER COLUMN id SET DEFAULT nextval('nic_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY node ALTER COLUMN id SET DEFAULT nextval('node_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY obm ALTER COLUMN id SET DEFAULT nextval('obm_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY port ALTER COLUMN id SET DEFAULT nextval('port_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY project ALTER COLUMN id SET DEFAULT nextval('project_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY switch ALTER COLUMN id SET DEFAULT nextval('switch_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: haas_dev
--

INSERT INTO alembic_version (version_num) VALUES ('b5b31d19257d');
INSERT INTO alembic_version (version_num) VALUES ('df8d9f423f2b');
INSERT INTO alembic_version (version_num) VALUES ('c45f6a96dbe7');


--
-- Data for Name: headnode; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: headnode_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('headnode_id_seq', 1, false);


--
-- Data for Name: hnic; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: hnic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('hnic_id_seq', 1, false);


--
-- Data for Name: metadata; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: metadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('metadata_id_seq', 1, false);


--
-- Data for Name: mock_obm; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Data for Name: mock_switch; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Data for Name: network; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Data for Name: network_attachment; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: network_attachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('network_attachment_id_seq', 1, false);


--
-- Name: network_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('network_id_seq', 1, false);


--
-- Data for Name: network_projects; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Data for Name: networking_action; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: networking_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('networking_action_id_seq', 1, false);


--
-- Data for Name: nic; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: nic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('nic_id_seq', 1, false);


--
-- Data for Name: node; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: node_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('node_id_seq', 1, false);


--
-- Data for Name: obm; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: obm_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('obm_id_seq', 1, false);


--
-- Data for Name: port; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: port_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('port_id_seq', 1, false);


--
-- Data for Name: project; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: project_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('project_id_seq', 1, false);


--
-- Data for Name: switch; Type: TABLE DATA; Schema: public; Owner: haas_dev
--



--
-- Name: switch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas_dev
--

SELECT pg_catalog.setval('switch_id_seq', 1, false);


--
-- Name: headnode_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_pkey PRIMARY KEY (id);


--
-- Name: headnode_uuid_key; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_uuid_key UNIQUE (uuid);


--
-- Name: hnic_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_pkey PRIMARY KEY (id);


--
-- Name: metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (id);


--
-- Name: mock_obm_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY mock_obm
    ADD CONSTRAINT mock_obm_pkey PRIMARY KEY (id);


--
-- Name: mock_switch_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY mock_switch
    ADD CONSTRAINT mock_switch_pkey PRIMARY KEY (id);


--
-- Name: network_attachment_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_pkey PRIMARY KEY (id);


--
-- Name: network_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_pkey PRIMARY KEY (id);


--
-- Name: networking_action_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_pkey PRIMARY KEY (id);


--
-- Name: nic_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_pkey PRIMARY KEY (id);


--
-- Name: node_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_pkey PRIMARY KEY (id);


--
-- Name: obm_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY obm
    ADD CONSTRAINT obm_pkey PRIMARY KEY (id);


--
-- Name: port_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY port
    ADD CONSTRAINT port_pkey PRIMARY KEY (id);


--
-- Name: project_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: switch_pkey; Type: CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY switch
    ADD CONSTRAINT switch_pkey PRIMARY KEY (id);


--
-- Name: headnode_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: hnic_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: hnic_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES headnode(id);


--
-- Name: metadata_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES node(id);


--
-- Name: mock_obm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY mock_obm
    ADD CONSTRAINT mock_obm_id_fkey FOREIGN KEY (id) REFERENCES obm(id);


--
-- Name: mock_switch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY mock_switch
    ADD CONSTRAINT mock_switch_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: network_attachment_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: network_attachment_nic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_nic_id_fkey FOREIGN KEY (nic_id) REFERENCES nic(id);


--
-- Name: network_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES project(id);


--
-- Name: network_projects_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network_projects
    ADD CONSTRAINT network_projects_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: network_projects_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY network_projects
    ADD CONSTRAINT network_projects_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: networking_action_new_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_new_network_id_fkey FOREIGN KEY (new_network_id) REFERENCES network(id);


--
-- Name: networking_action_nic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_nic_id_fkey FOREIGN KEY (nic_id) REFERENCES nic(id);


--
-- Name: nic_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES node(id);


--
-- Name: nic_port_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_port_id_fkey FOREIGN KEY (port_id) REFERENCES port(id);


--
-- Name: node_obm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_obm_id_fkey FOREIGN KEY (obm_id) REFERENCES obm(id);


--
-- Name: node_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: port_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas_dev
--

ALTER TABLE ONLY port
    ADD CONSTRAINT port_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES switch(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--



--
-- PostgreSQL database dump complete
--

