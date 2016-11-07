--
-- PostgreSQL database dump
--
-- This corresponds to a database generated with the schema as of the flask
-- routing integration. The exact commit in question is:
--
-- a22797022529a40c96f038641a267829c7b69670
--
-- The extensions loaded were:
--
--
-- * haas.ext.switches.mock
-- * haas.ext.switches.nexus
-- * haas.ext.switches.dell
-- * haas.ext.obm.ipmi
-- * haas.ext.obm.mock
-- * haas.ext.auth.database
-- * haas.ext.network_allocators.vlan_pool
--
-- Additionally, haas.cfg contained the following, which affects the generated
-- database:
--
--   [haas.ext.network_allocators.vlan_pool]
--   vlans = 100-200, 300-500
--
-- The database was poplated with objects equivalent to those created by
-- `haas.test_common.initial_db` as of the commit:
--
-- e8a7f545eb7b3afe3c39169becef1633f507d349

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;


SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: headnode; Type: TABLE; Schema: public; Owner: haas; Tablespace:
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
-- Name: headnode_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE headnode_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: headnode_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE headnode_id_seq OWNED BY headnode.id;


--
-- Name: hnic; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE hnic (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL,
    network_id integer
);


--
-- Name: hnic_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE hnic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: hnic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE hnic_id_seq OWNED BY hnic.id;


--
-- Name: ipmi; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE ipmi (
    id integer NOT NULL,
    host character varying NOT NULL,
    "user" character varying NOT NULL,
    password character varying NOT NULL
);


--
-- Name: mockobm; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE mockobm (
    id integer NOT NULL,
    host character varying NOT NULL,
    "user" character varying NOT NULL,
    password character varying NOT NULL
);


--
-- Name: mockswitch; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE mockswitch (
    id integer NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL
);


--
-- Name: network; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE network (
    id integer NOT NULL,
    label character varying NOT NULL,
    creator_id integer,
    access_id integer,
    allocated boolean,
    network_id character varying NOT NULL
);


--
-- Name: network_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE network_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: network_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE network_id_seq OWNED BY network.id;


--
-- Name: networkattachment; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE networkattachment (
    id integer NOT NULL,
    nic_id integer NOT NULL,
    network_id integer NOT NULL,
    channel character varying NOT NULL
);


--
-- Name: networkattachment_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE networkattachment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: networkattachment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE networkattachment_id_seq OWNED BY networkattachment.id;


--
-- Name: networkingaction; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE networkingaction (
    id integer NOT NULL,
    nic_id integer NOT NULL,
    new_network_id integer,
    channel character varying NOT NULL
);


--
-- Name: networkingaction_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE networkingaction_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: networkingaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE networkingaction_id_seq OWNED BY networkingaction.id;


--
-- Name: nexus; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE nexus (
    id integer NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL,
    dummy_vlan character varying NOT NULL
);


--
-- Name: nic; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE nic (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL,
    mac_addr character varying,
    port_id integer
);


--
-- Name: nic_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE nic_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: nic_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE nic_id_seq OWNED BY nic.id;


--
-- Name: node; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE node (
    id integer NOT NULL,
    label character varying NOT NULL,
    project_id integer,
    obm_id integer NOT NULL
);


--
-- Name: node_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE node_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: node_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE node_id_seq OWNED BY node.id;


--
-- Name: obm; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE obm (
    id integer NOT NULL,
    type character varying NOT NULL
);


--
-- Name: obm_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE obm_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: obm_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE obm_id_seq OWNED BY obm.id;


--
-- Name: port; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE port (
    id integer NOT NULL,
    label character varying NOT NULL,
    owner_id integer NOT NULL
);


--
-- Name: port_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE port_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: port_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE port_id_seq OWNED BY port.id;


--
-- Name: powerconnect55xx; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE powerconnect55xx (
    id integer NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL
);


--
-- Name: project; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE project (
    id integer NOT NULL,
    label character varying NOT NULL
);


--
-- Name: project_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE project_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: project_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE project_id_seq OWNED BY project.id;


--
-- Name: switch; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE switch (
    id integer NOT NULL,
    label character varying NOT NULL,
    type character varying NOT NULL
);


--
-- Name: switch_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE switch_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: switch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE switch_id_seq OWNED BY switch.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE "user" (
    id integer NOT NULL,
    label character varying NOT NULL,
    is_admin boolean NOT NULL,
    hashed_password character varying
);



--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE user_id_seq OWNED BY "user".id;


--
-- Name: user_projects; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE user_projects (
    user_id integer,
    project_id integer
);



--
-- Name: vlan; Type: TABLE; Schema: public; Owner: haas; Tablespace:
--

CREATE TABLE vlan (
    id integer NOT NULL,
    vlan_no integer NOT NULL,
    available boolean NOT NULL
);



--
-- Name: vlan_id_seq; Type: SEQUENCE; Schema: public; Owner: haas
--

CREATE SEQUENCE vlan_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: vlan_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: haas
--

ALTER SEQUENCE vlan_id_seq OWNED BY vlan.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY headnode ALTER COLUMN id SET DEFAULT nextval('headnode_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY hnic ALTER COLUMN id SET DEFAULT nextval('hnic_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY network ALTER COLUMN id SET DEFAULT nextval('network_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY networkattachment ALTER COLUMN id SET DEFAULT nextval('networkattachment_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY networkingaction ALTER COLUMN id SET DEFAULT nextval('networkingaction_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY nic ALTER COLUMN id SET DEFAULT nextval('nic_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY node ALTER COLUMN id SET DEFAULT nextval('node_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY obm ALTER COLUMN id SET DEFAULT nextval('obm_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY port ALTER COLUMN id SET DEFAULT nextval('port_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY project ALTER COLUMN id SET DEFAULT nextval('project_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY switch ALTER COLUMN id SET DEFAULT nextval('switch_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY "user" ALTER COLUMN id SET DEFAULT nextval('user_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: haas
--

ALTER TABLE ONLY vlan ALTER COLUMN id SET DEFAULT nextval('vlan_id_seq'::regclass);


--
-- Data for Name: headnode; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO headnode (id, label, project_id, dirty, base_img, uuid) VALUES (1, 'runway_headnode_on', 1, false, 'base-headnode', 'e9c77c00-fa31-11e5-93f8-001e65327848');
INSERT INTO headnode (id, label, project_id, dirty, base_img, uuid) VALUES (2, 'runway_headnode_off', 1, true, 'base-headnode', 'e9d05ed8-fa31-11e5-93f8-001e65327848');
INSERT INTO headnode (id, label, project_id, dirty, base_img, uuid) VALUES (3, 'runway_manhattan_on', 2, false, 'base-headnode', 'e9d1f02c-fa31-11e5-93f8-001e65327848');
INSERT INTO headnode (id, label, project_id, dirty, base_img, uuid) VALUES (4, 'runway_manhattan_off', 2, true, 'base-headnode', 'e9d358b8-fa31-11e5-93f8-001e65327848');


--
-- Name: headnode_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('headnode_id_seq', 4, true);


--
-- Data for Name: hnic; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO hnic (id, label, owner_id, network_id) VALUES (1, 'pxe', 1, NULL);
INSERT INTO hnic (id, label, owner_id, network_id) VALUES (2, 'public', 1, 3);
INSERT INTO hnic (id, label, owner_id, network_id) VALUES (3, 'pxe', 2, NULL);
INSERT INTO hnic (id, label, owner_id, network_id) VALUES (4, 'public', 2, 3);
INSERT INTO hnic (id, label, owner_id, network_id) VALUES (5, 'pxe', 3, NULL);
INSERT INTO hnic (id, label, owner_id, network_id) VALUES (6, 'public', 3, 3);
INSERT INTO hnic (id, label, owner_id, network_id) VALUES (7, 'pxe', 4, NULL);
INSERT INTO hnic (id, label, owner_id, network_id) VALUES (8, 'public', 4, 3);


--
-- Name: hnic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('hnic_id_seq', 8, true);


--
-- Data for Name: ipmi; Type: TABLE DATA; Schema: public; Owner: haas
--



--
-- Data for Name: mockobm; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO mockobm (id, host, "user", password) VALUES (1, 'runway_node_0', 'user', 'password');
INSERT INTO mockobm (id, host, "user", password) VALUES (2, 'runway_node_1', 'user', 'password');
INSERT INTO mockobm (id, host, "user", password) VALUES (3, 'manhattan_node_0', 'user', 'password');
INSERT INTO mockobm (id, host, "user", password) VALUES (4, 'manhattan_node_1', 'user', 'password');
INSERT INTO mockobm (id, host, "user", password) VALUES (5, 'free_node_0', 'user', 'password');
INSERT INTO mockobm (id, host, "user", password) VALUES (6, 'free_node_1', 'user', 'password');
INSERT INTO mockobm (id, host, "user", password) VALUES (7, 'hostname', 'user', 'password');


--
-- Data for Name: mockswitch; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO mockswitch (id, hostname, username, password) VALUES (1, 'empty', 'alice', 'secret');
INSERT INTO mockswitch (id, hostname, username, password) VALUES (2, 'stock', 'bob', 'password');


--
-- Data for Name: network; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO network (id, label, creator_id, access_id, allocated, network_id) VALUES (1, 'stock_int_pub', NULL, NULL, true, '100');
INSERT INTO network (id, label, creator_id, access_id, allocated, network_id) VALUES (2, 'stock_ext_pub', NULL, NULL, false, 'ext_pub_chan');
INSERT INTO network (id, label, creator_id, access_id, allocated, network_id) VALUES (3, 'pub_default', NULL, NULL, true, '101');
INSERT INTO network (id, label, creator_id, access_id, allocated, network_id) VALUES (4, 'runway_pxe', 1, 1, true, '102');
INSERT INTO network (id, label, creator_id, access_id, allocated, network_id) VALUES (5, 'runway_provider', NULL, 1, false, 'runway_provider_chan');
INSERT INTO network (id, label, creator_id, access_id, allocated, network_id) VALUES (6, 'manhattan_pxe', 2, 2, true, '103');
INSERT INTO network (id, label, creator_id, access_id, allocated, network_id) VALUES (7, 'manhattan_provider', NULL, 2, false, 'manhattan_provider_chan');


--
-- Name: network_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('network_id_seq', 7, true);


--
-- Data for Name: networkattachment; Type: TABLE DATA; Schema: public; Owner: haas
--



--
-- Name: networkattachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('networkattachment_id_seq', 1, false);


--
-- Data for Name: networkingaction; Type: TABLE DATA; Schema: public; Owner: haas
--



--
-- Name: networkingaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('networkingaction_id_seq', 1, false);


--
-- Data for Name: nexus; Type: TABLE DATA; Schema: public; Owner: haas
--



--
-- Data for Name: nic; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (1, 'boot-nic', 1, 'Unknown', NULL);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (2, 'nic-with-port', 1, 'Unknown', 3);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (3, 'boot-nic', 2, 'Unknown', NULL);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (4, 'nic-with-port', 2, 'Unknown', 4);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (5, 'boot-nic', 3, 'Unknown', NULL);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (6, 'nic-with-port', 3, 'Unknown', 5);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (7, 'boot-nic', 4, 'Unknown', NULL);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (8, 'nic-with-port', 4, 'Unknown', 6);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (9, 'boot-nic', 5, 'Unknown', NULL);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (10, 'nic-with-port', 5, 'Unknown', 7);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (11, 'boot-nic', 6, 'Unknown', NULL);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (12, 'nic-with-port', 6, 'Unknown', 8);


--
-- Name: nic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('nic_id_seq', 12, true);


--
-- Data for Name: node; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO node (id, label, project_id, obm_id) VALUES (1, 'runway_node_0', 1, 1);
INSERT INTO node (id, label, project_id, obm_id) VALUES (2, 'runway_node_1', 1, 2);
INSERT INTO node (id, label, project_id, obm_id) VALUES (3, 'manhattan_node_0', 2, 3);
INSERT INTO node (id, label, project_id, obm_id) VALUES (4, 'manhattan_node_1', 2, 4);
INSERT INTO node (id, label, project_id, obm_id) VALUES (5, 'free_node_0', NULL, 5);
INSERT INTO node (id, label, project_id, obm_id) VALUES (6, 'free_node_1', NULL, 6);
INSERT INTO node (id, label, project_id, obm_id) VALUES (7, 'no_nic_node', NULL, 7);


--
-- Name: node_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('node_id_seq', 7, true);


--
-- Data for Name: obm; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO obm (id, type) VALUES (1, 'http://schema.massopencloud.org/haas/v0/obm/mock');
INSERT INTO obm (id, type) VALUES (2, 'http://schema.massopencloud.org/haas/v0/obm/mock');
INSERT INTO obm (id, type) VALUES (3, 'http://schema.massopencloud.org/haas/v0/obm/mock');
INSERT INTO obm (id, type) VALUES (4, 'http://schema.massopencloud.org/haas/v0/obm/mock');
INSERT INTO obm (id, type) VALUES (5, 'http://schema.massopencloud.org/haas/v0/obm/mock');
INSERT INTO obm (id, type) VALUES (6, 'http://schema.massopencloud.org/haas/v0/obm/mock');
INSERT INTO obm (id, type) VALUES (7, 'http://schema.massopencloud.org/haas/v0/obm/mock');


--
-- Name: obm_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('obm_id_seq', 7, true);


--
-- Data for Name: port; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO port (id, label, owner_id) VALUES (1, 'free_port_0', 2);
INSERT INTO port (id, label, owner_id) VALUES (2, 'free_port_1', 2);
INSERT INTO port (id, label, owner_id) VALUES (3, 'runway_node_0_port', 2);
INSERT INTO port (id, label, owner_id) VALUES (4, 'runway_node_1_port', 2);
INSERT INTO port (id, label, owner_id) VALUES (5, 'manhattan_node_0_port', 2);
INSERT INTO port (id, label, owner_id) VALUES (6, 'manhattan_node_1_port', 2);
INSERT INTO port (id, label, owner_id) VALUES (7, 'free_node_0_port', 2);
INSERT INTO port (id, label, owner_id) VALUES (8, 'free_node_1_port', 2);


--
-- Name: port_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('port_id_seq', 8, true);


--
-- Data for Name: powerconnect55xx; Type: TABLE DATA; Schema: public; Owner: haas
--



--
-- Data for Name: project; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO project (id, label) VALUES (1, 'runway');
INSERT INTO project (id, label) VALUES (2, 'manhattan');
INSERT INTO project (id, label) VALUES (3, 'empty-project');


--
-- Name: project_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('project_id_seq', 3, true);


--
-- Data for Name: switch; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO switch (id, label, type) VALUES (1, 'empty-switch', 'http://schema.massopencloud.org/haas/v0/switches/mock');
INSERT INTO switch (id, label, type) VALUES (2, 'stock_switch_0', 'http://schema.massopencloud.org/haas/v0/switches/mock');


--
-- Name: switch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('switch_id_seq', 2, true);


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: haas
--



--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('user_id_seq', 1, false);


--
-- Data for Name: user_projects; Type: TABLE DATA; Schema: public; Owner: haas
--



--
-- Data for Name: vlan; Type: TABLE DATA; Schema: public; Owner: haas
--

INSERT INTO vlan (id, vlan_no, available) VALUES (5, 104, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (6, 105, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (7, 106, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (8, 107, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (9, 108, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (10, 109, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (11, 110, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (12, 111, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (13, 112, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (14, 113, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (15, 114, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (16, 115, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (17, 116, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (18, 117, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (19, 118, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (20, 119, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (21, 120, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (22, 121, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (23, 122, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (24, 123, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (25, 124, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (26, 125, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (27, 126, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (28, 127, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (29, 128, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (30, 129, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (31, 130, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (32, 131, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (33, 132, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (34, 133, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (35, 134, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (36, 135, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (37, 136, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (38, 137, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (39, 138, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (40, 139, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (41, 140, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (42, 141, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (43, 142, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (44, 143, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (45, 144, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (46, 145, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (47, 146, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (48, 147, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (49, 148, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (50, 149, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (51, 150, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (52, 151, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (53, 152, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (54, 153, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (55, 154, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (56, 155, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (57, 156, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (58, 157, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (59, 158, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (60, 159, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (61, 160, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (62, 161, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (63, 162, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (64, 163, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (65, 164, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (66, 165, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (67, 166, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (68, 167, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (69, 168, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (70, 169, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (71, 170, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (72, 171, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (73, 172, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (74, 173, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (75, 174, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (76, 175, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (77, 176, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (78, 177, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (79, 178, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (80, 179, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (81, 180, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (82, 181, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (83, 182, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (84, 183, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (85, 184, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (86, 185, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (87, 186, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (88, 187, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (89, 188, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (90, 189, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (91, 190, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (92, 191, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (93, 192, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (94, 193, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (95, 194, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (96, 195, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (97, 196, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (98, 197, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (99, 198, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (100, 199, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (101, 200, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (102, 300, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (103, 301, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (104, 302, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (105, 303, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (106, 304, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (107, 305, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (108, 306, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (109, 307, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (110, 308, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (111, 309, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (112, 310, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (113, 311, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (114, 312, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (115, 313, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (116, 314, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (117, 315, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (118, 316, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (119, 317, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (120, 318, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (121, 319, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (122, 320, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (123, 321, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (124, 322, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (125, 323, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (126, 324, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (127, 325, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (128, 326, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (129, 327, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (130, 328, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (131, 329, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (132, 330, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (133, 331, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (134, 332, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (135, 333, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (136, 334, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (137, 335, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (138, 336, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (139, 337, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (140, 338, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (141, 339, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (142, 340, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (143, 341, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (144, 342, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (145, 343, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (146, 344, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (147, 345, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (148, 346, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (149, 347, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (150, 348, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (151, 349, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (152, 350, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (153, 351, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (154, 352, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (155, 353, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (156, 354, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (157, 355, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (158, 356, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (159, 357, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (160, 358, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (161, 359, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (162, 360, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (163, 361, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (164, 362, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (165, 363, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (166, 364, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (167, 365, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (168, 366, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (169, 367, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (170, 368, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (171, 369, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (172, 370, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (173, 371, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (174, 372, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (175, 373, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (176, 374, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (177, 375, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (178, 376, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (179, 377, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (180, 378, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (181, 379, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (182, 380, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (183, 381, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (184, 382, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (185, 383, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (186, 384, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (187, 385, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (188, 386, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (189, 387, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (190, 388, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (191, 389, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (192, 390, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (193, 391, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (194, 392, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (195, 393, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (196, 394, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (197, 395, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (198, 396, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (199, 397, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (200, 398, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (201, 399, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (202, 400, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (203, 401, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (204, 402, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (205, 403, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (206, 404, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (207, 405, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (208, 406, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (209, 407, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (210, 408, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (211, 409, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (212, 410, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (213, 411, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (214, 412, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (215, 413, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (216, 414, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (217, 415, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (218, 416, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (219, 417, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (220, 418, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (221, 419, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (222, 420, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (223, 421, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (224, 422, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (225, 423, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (226, 424, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (227, 425, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (228, 426, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (229, 427, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (230, 428, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (231, 429, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (232, 430, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (233, 431, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (234, 432, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (235, 433, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (236, 434, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (237, 435, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (238, 436, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (239, 437, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (240, 438, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (241, 439, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (242, 440, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (243, 441, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (244, 442, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (245, 443, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (246, 444, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (247, 445, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (248, 446, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (249, 447, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (250, 448, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (251, 449, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (252, 450, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (253, 451, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (254, 452, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (255, 453, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (256, 454, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (257, 455, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (258, 456, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (259, 457, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (260, 458, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (261, 459, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (262, 460, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (263, 461, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (264, 462, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (265, 463, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (266, 464, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (267, 465, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (268, 466, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (269, 467, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (270, 468, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (271, 469, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (272, 470, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (273, 471, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (274, 472, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (275, 473, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (276, 474, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (277, 475, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (278, 476, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (279, 477, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (280, 478, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (281, 479, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (282, 480, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (283, 481, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (284, 482, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (285, 483, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (286, 484, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (287, 485, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (288, 486, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (289, 487, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (290, 488, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (291, 489, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (292, 490, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (293, 491, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (294, 492, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (295, 493, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (296, 494, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (297, 495, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (298, 496, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (299, 497, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (300, 498, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (301, 499, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (302, 500, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (1, 100, false);
INSERT INTO vlan (id, vlan_no, available) VALUES (2, 101, false);
INSERT INTO vlan (id, vlan_no, available) VALUES (3, 102, false);
INSERT INTO vlan (id, vlan_no, available) VALUES (4, 103, false);


--
-- Name: vlan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: haas
--

SELECT pg_catalog.setval('vlan_id_seq', 302, true);


--
-- Name: headnode_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_pkey PRIMARY KEY (id);


--
-- Name: headnode_uuid_key; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_uuid_key UNIQUE (uuid);


--
-- Name: hnic_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_pkey PRIMARY KEY (id);


--
-- Name: ipmi_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY ipmi
    ADD CONSTRAINT ipmi_pkey PRIMARY KEY (id);


--
-- Name: mockobm_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY mockobm
    ADD CONSTRAINT mockobm_pkey PRIMARY KEY (id);


--
-- Name: mockswitch_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY mockswitch
    ADD CONSTRAINT mockswitch_pkey PRIMARY KEY (id);


--
-- Name: network_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_pkey PRIMARY KEY (id);


--
-- Name: networkattachment_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY networkattachment
    ADD CONSTRAINT networkattachment_pkey PRIMARY KEY (id);


--
-- Name: networkingaction_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY networkingaction
    ADD CONSTRAINT networkingaction_pkey PRIMARY KEY (id);


--
-- Name: nexus_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY nexus
    ADD CONSTRAINT nexus_pkey PRIMARY KEY (id);


--
-- Name: nic_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_pkey PRIMARY KEY (id);


--
-- Name: node_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_pkey PRIMARY KEY (id);


--
-- Name: obm_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY obm
    ADD CONSTRAINT obm_pkey PRIMARY KEY (id);


--
-- Name: port_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY port
    ADD CONSTRAINT port_pkey PRIMARY KEY (id);


--
-- Name: powerconnect55xx_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY powerconnect55xx
    ADD CONSTRAINT powerconnect55xx_pkey PRIMARY KEY (id);


--
-- Name: project_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: switch_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY switch
    ADD CONSTRAINT switch_pkey PRIMARY KEY (id);


--
-- Name: user_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: vlan_pkey; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY vlan
    ADD CONSTRAINT vlan_pkey PRIMARY KEY (id);


--
-- Name: vlan_vlan_no_key; Type: CONSTRAINT; Schema: public; Owner: haas; Tablespace:
--

ALTER TABLE ONLY vlan
    ADD CONSTRAINT vlan_vlan_no_key UNIQUE (vlan_no);


--
-- Name: headnode_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: hnic_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: hnic_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES headnode(id);


--
-- Name: ipmi_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY ipmi
    ADD CONSTRAINT ipmi_id_fkey FOREIGN KEY (id) REFERENCES obm(id);


--
-- Name: mockobm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY mockobm
    ADD CONSTRAINT mockobm_id_fkey FOREIGN KEY (id) REFERENCES obm(id);


--
-- Name: mockswitch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY mockswitch
    ADD CONSTRAINT mockswitch_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: network_access_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_access_id_fkey FOREIGN KEY (access_id) REFERENCES project(id);


--
-- Name: network_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES project(id);


--
-- Name: networkattachment_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY networkattachment
    ADD CONSTRAINT networkattachment_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: networkattachment_nic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY networkattachment
    ADD CONSTRAINT networkattachment_nic_id_fkey FOREIGN KEY (nic_id) REFERENCES nic(id);


--
-- Name: networkingaction_new_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY networkingaction
    ADD CONSTRAINT networkingaction_new_network_id_fkey FOREIGN KEY (new_network_id) REFERENCES network(id);


--
-- Name: networkingaction_nic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY networkingaction
    ADD CONSTRAINT networkingaction_nic_id_fkey FOREIGN KEY (nic_id) REFERENCES nic(id);


--
-- Name: nexus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY nexus
    ADD CONSTRAINT nexus_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: nic_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES node(id);


--
-- Name: nic_port_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_port_id_fkey FOREIGN KEY (port_id) REFERENCES port(id);


--
-- Name: node_obm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_obm_id_fkey FOREIGN KEY (obm_id) REFERENCES obm(id);


--
-- Name: node_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: port_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY port
    ADD CONSTRAINT port_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES switch(id);


--
-- Name: powerconnect55xx_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY powerconnect55xx
    ADD CONSTRAINT powerconnect55xx_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: user_projects_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY user_projects
    ADD CONSTRAINT user_projects_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: user_projects_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: haas
--

ALTER TABLE ONLY user_projects
    ADD CONSTRAINT user_projects_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);


--
-- PostgreSQL database dump complete
--
