--
-- PostgreSQL database dump
--
-- This corresponds to the schema shortly before the introduction of a `type`
-- field to the networking_action table. Its key feature is the inclusion of
-- pending actions. The exact commit in question is:
--
-- 41ce4dd6a50eece231c0531b4f161fc65f0004a7
--
-- The extensions loaded were:
--
-- * haas.ext.switches.mock
-- * haas.ext.obm.mock
-- * haas.ext.auth.null
-- * haas.ext.network_allocators.null
--
-- The database was populated with objects equivalent to those created by
-- `create_pending_actions_db` in `tests/unit/migrations.py`, as of the
-- commit:
--
-- be03e9938a846004d45b3bb7be98ac539451f057

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: headnode; Type: TABLE; Schema: public; Owner: hil
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
-- Name: headnode_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE headnode_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: headnode_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE headnode_id_seq OWNED BY headnode.id;


--
-- Name: hnic; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE hnic (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL,
    network_id integer
);



--
-- Name: hnic_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE hnic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: hnic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE hnic_id_seq OWNED BY hnic.id;


--
-- Name: mock_obm; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE mock_obm (
    id integer NOT NULL,
    host character varying NOT NULL,
    "user" character varying NOT NULL,
    password character varying NOT NULL
);



--
-- Name: mock_switch; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE mock_switch (
    id integer NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL
);



--
-- Name: network; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE network (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer,
    allocated boolean,
    network_id character varying NOT NULL
);



--
-- Name: network_attachment; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE network_attachment (
    id integer NOT NULL,
    nic_id integer NOT NULL,
    network_id integer NOT NULL,
    channel character varying NOT NULL
);



--
-- Name: network_attachment_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE network_attachment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: network_attachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE network_attachment_id_seq OWNED BY network_attachment.id;


--
-- Name: network_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE network_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: network_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE network_id_seq OWNED BY network.id;


--
-- Name: network_projects; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE network_projects (
    project_id integer,
    network_id integer
);



--
-- Name: networking_action; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE networking_action (
    id integer NOT NULL,
    nic_id integer NOT NULL,
    new_network_id integer,
    channel character varying NOT NULL
);



--
-- Name: networking_action_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE networking_action_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: networking_action_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE networking_action_id_seq OWNED BY networking_action.id;


--
-- Name: nic; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE nic (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL,
    mac_addr character varying,
    port_id integer
);



--
-- Name: nic_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE nic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: nic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE nic_id_seq OWNED BY nic.id;


--
-- Name: node; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE node (
    id integer NOT NULL,
    label character varying NOT NULL,
    project_id integer,
    obm_id integer NOT NULL
);



--
-- Name: node_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE node_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: node_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE node_id_seq OWNED BY node.id;


--
-- Name: obm; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE obm (
    id integer NOT NULL,
    type character varying NOT NULL
);



--
-- Name: obm_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE obm_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: obm_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE obm_id_seq OWNED BY obm.id;


--
-- Name: port; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE port (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL
);



--
-- Name: port_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE port_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: port_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE port_id_seq OWNED BY port.id;


--
-- Name: project; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE project (
    id integer NOT NULL,
    label character varying NOT NULL
);



--
-- Name: project_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE project_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: project_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE project_id_seq OWNED BY project.id;


--
-- Name: switch; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE switch (
    id integer NOT NULL,
    label character varying NOT NULL,
    type character varying NOT NULL
);



--
-- Name: switch_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE switch_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


-- Name: switch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE switch_id_seq OWNED BY switch.id;


--
-- Name: headnode id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY headnode ALTER COLUMN id SET DEFAULT nextval('headnode_id_seq'::regclass);


--
-- Name: hnic id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY hnic ALTER COLUMN id SET DEFAULT nextval('hnic_id_seq'::regclass);


--
-- Name: network id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network ALTER COLUMN id SET DEFAULT nextval('network_id_seq'::regclass);


--
-- Name: network_attachment id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_attachment ALTER COLUMN id SET DEFAULT nextval('network_attachment_id_seq'::regclass);


--
-- Name: networking_action id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY networking_action ALTER COLUMN id SET DEFAULT nextval('networking_action_id_seq'::regclass);


--
-- Name: nic id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nic ALTER COLUMN id SET DEFAULT nextval('nic_id_seq'::regclass);


--
-- Name: node id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY node ALTER COLUMN id SET DEFAULT nextval('node_id_seq'::regclass);


--
-- Name: obm id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY obm ALTER COLUMN id SET DEFAULT nextval('obm_id_seq'::regclass);


--
-- Name: port id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY port ALTER COLUMN id SET DEFAULT nextval('port_id_seq'::regclass);


--
-- Name: project id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY project ALTER COLUMN id SET DEFAULT nextval('project_id_seq'::regclass);


--
-- Name: switch id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY switch ALTER COLUMN id SET DEFAULT nextval('switch_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO alembic_version (version_num) VALUES ('89630e3872ec');
INSERT INTO alembic_version (version_num) VALUES ('b5b31d19257d');
INSERT INTO alembic_version (version_num) VALUES ('df8d9f423f2b');


--
-- Data for Name: headnode; Type: TABLE DATA; Schema: public; Owner: hil
--



--
-- Name: headnode_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('headnode_id_seq', 1, false);


--
-- Data for Name: hnic; Type: TABLE DATA; Schema: public; Owner: hil
--



--
-- Name: hnic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('hnic_id_seq', 1, false);


--
-- Data for Name: mock_obm; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO mock_obm (id, host, "user", password) VALUES (1, 'host', 'user', 'pass');


--
-- Data for Name: mock_switch; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO mock_switch (id, hostname, username, password) VALUES (1, 'host', 'user', 'pass');


--
-- Data for Name: network; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO network (id, label, owner_id, allocated, network_id) VALUES (1, 'runway_pxe', 1, true, '8d85b688-cd57-11e6-95c9-001e65327848');


--
-- Data for Name: network_attachment; Type: TABLE DATA; Schema: public; Owner: hil
--



--
-- Name: network_attachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('network_attachment_id_seq', 1, false);


--
-- Name: network_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('network_id_seq', 1, true);


--
-- Data for Name: network_projects; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO network_projects (project_id, network_id) VALUES (1, 1);


--
-- Data for Name: networking_action; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO networking_action (id, nic_id, new_network_id, channel) VALUES (1, 1, 1, 'null');


--
-- Name: networking_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('networking_action_id_seq', 1, true);


--
-- Data for Name: nic; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (1, 'pxe', 1, 'de:ad:be:ef:20:16', 1);


--
-- Name: nic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('nic_id_seq', 1, true);


--
-- Data for Name: node; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO node (id, label, project_id, obm_id) VALUES (1, 'node-1', 1, 1);


--
-- Name: node_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('node_id_seq', 1, true);


--
-- Data for Name: obm; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO obm (id, type) VALUES (1, 'http://schema.massopencloud.org/haas/v0/obm/mock');


--
-- Name: obm_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('obm_id_seq', 1, true);


--
-- Data for Name: port; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO port (id, label, owner_id) VALUES (1, 'gi1/0/4', 1);


--
-- Name: port_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('port_id_seq', 1, true);


--
-- Data for Name: project; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO project (id, label) VALUES (1, 'runway');


--
-- Name: project_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('project_id_seq', 1, true);


--
-- Data for Name: switch; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO switch (id, label, type) VALUES (1, 'sw0', 'http://schema.massopencloud.org/haas/v0/switches/mock');


--
-- Name: switch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('switch_id_seq', 1, true);


--
-- Name: headnode headnode_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_pkey PRIMARY KEY (id);


--
-- Name: headnode headnode_uuid_key; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_uuid_key UNIQUE (uuid);


--
-- Name: hnic hnic_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_pkey PRIMARY KEY (id);


--
-- Name: mock_obm mock_obm_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY mock_obm
    ADD CONSTRAINT mock_obm_pkey PRIMARY KEY (id);


--
-- Name: mock_switch mock_switch_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY mock_switch
    ADD CONSTRAINT mock_switch_pkey PRIMARY KEY (id);


--
-- Name: network_attachment network_attachment_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_pkey PRIMARY KEY (id);


--
-- Name: network network_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_pkey PRIMARY KEY (id);


--
-- Name: networking_action networking_action_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_pkey PRIMARY KEY (id);


--
-- Name: nic nic_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_pkey PRIMARY KEY (id);


--
-- Name: node node_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_pkey PRIMARY KEY (id);


--
-- Name: obm obm_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY obm
    ADD CONSTRAINT obm_pkey PRIMARY KEY (id);


--
-- Name: port port_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY port
    ADD CONSTRAINT port_pkey PRIMARY KEY (id);


--
-- Name: project project_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: switch switch_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY switch
    ADD CONSTRAINT switch_pkey PRIMARY KEY (id);


--
-- Name: headnode headnode_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: hnic hnic_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: hnic hnic_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES headnode(id);


--
-- Name: mock_obm mock_obm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY mock_obm
    ADD CONSTRAINT mock_obm_id_fkey FOREIGN KEY (id) REFERENCES obm(id);


--
-- Name: mock_switch mock_switch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY mock_switch
    ADD CONSTRAINT mock_switch_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: network_attachment network_attachment_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: network_attachment network_attachment_nic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_nic_id_fkey FOREIGN KEY (nic_id) REFERENCES nic(id);


--
-- Name: network network_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES project(id);


--
-- Name: network_projects network_projects_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_projects
    ADD CONSTRAINT network_projects_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: network_projects network_projects_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_projects
    ADD CONSTRAINT network_projects_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: networking_action networking_action_new_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_new_network_id_fkey FOREIGN KEY (new_network_id) REFERENCES network(id);


--
-- Name: networking_action networking_action_nic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_nic_id_fkey FOREIGN KEY (nic_id) REFERENCES nic(id);


--
-- Name: nic nic_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES node(id);


--
-- Name: nic nic_port_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_port_id_fkey FOREIGN KEY (port_id) REFERENCES port(id);


--
-- Name: node node_obm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_obm_id_fkey FOREIGN KEY (obm_id) REFERENCES obm(id);


--
-- Name: node node_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: port port_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY port
    ADD CONSTRAINT port_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES switch(id);


--
-- PostgreSQL database dump complete
--

