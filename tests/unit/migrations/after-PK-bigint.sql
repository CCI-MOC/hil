--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.7
-- Dumped by pg_dump version 9.5.7

SET statement_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;

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
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE alembic_version (
    version_num character varying(32) NOT NULL
);



--
-- Name: brocade; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE brocade (
    id bigint NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL,
    interface_type character varying NOT NULL
);



--
-- Name: dell_n3000; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE dell_n3000 (
    id bigint NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL,
    dummy_vlan character varying NOT NULL
);



--
-- Name: headnode; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE headnode (
    id bigint NOT NULL,
    label character varying NOT NULL,
    project_id bigint NOT NULL,
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
    id bigint NOT NULL,
    label character varying NOT NULL,
    owner_id bigint NOT NULL,
    network_id bigint
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
-- Name: ipmi; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE ipmi (
    id bigint NOT NULL,
    host character varying NOT NULL,
    "user" character varying NOT NULL,
    password character varying NOT NULL
);



--
-- Name: metadata; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE metadata (
    id bigint NOT NULL,
    label character varying NOT NULL,
    value character varying,
    owner_id bigint NOT NULL
);



--
-- Name: metadata_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE metadata_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: metadata_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE metadata_id_seq OWNED BY metadata.id;


--
-- Name: mock_obm; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE mock_obm (
    id bigint NOT NULL,
    host character varying NOT NULL,
    "user" character varying NOT NULL,
    password character varying NOT NULL
);



--
-- Name: mock_switch; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE mock_switch (
    id bigint NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL
);



--
-- Name: network; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE network (
    id bigint NOT NULL,
    label character varying NOT NULL,
    owner_id bigint,
    allocated boolean,
    network_id character varying NOT NULL
);



--
-- Name: network_attachment; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE network_attachment (
    id bigint NOT NULL,
    nic_id bigint NOT NULL,
    network_id bigint NOT NULL,
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
    project_id bigint,
    network_id bigint
);



--
-- Name: networking_action; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE networking_action (
    id bigint NOT NULL,
    type character varying NOT NULL,
    nic_id bigint NOT NULL,
    new_network_id bigint,
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
-- Name: nexus; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE nexus (
    id bigint NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL,
    dummy_vlan character varying NOT NULL
);



--
-- Name: nic; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE nic (
    id bigint NOT NULL,
    label character varying NOT NULL,
    owner_id bigint NOT NULL,
    mac_addr character varying,
    port_id bigint
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
    id bigint NOT NULL,
    label character varying NOT NULL,
    project_id bigint,
    obm_id bigint NOT NULL
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
    id bigint NOT NULL,
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
    id bigint NOT NULL,
    label character varying NOT NULL,
    owner_id bigint NOT NULL
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
-- Name: power_connect55xx; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE power_connect55xx (
    id bigint NOT NULL,
    hostname character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL
);



--
-- Name: project; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE project (
    id bigint NOT NULL,
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
    id bigint NOT NULL,
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



--
-- Name: switch_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE switch_id_seq OWNED BY switch.id;


--
-- Name: user; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE "user" (
    id bigint NOT NULL,
    label character varying NOT NULL,
    is_admin boolean NOT NULL,
    hashed_password character varying
);



--
-- Name: user_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE user_id_seq OWNED BY "user".id;


--
-- Name: user_projects; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE user_projects (
    user_id bigint,
    project_id bigint
);



--
-- Name: vlan; Type: TABLE; Schema: public; Owner: hil
--

CREATE TABLE vlan (
    id bigint NOT NULL,
    vlan_no integer NOT NULL,
    available boolean NOT NULL
);



--
-- Name: vlan_id_seq; Type: SEQUENCE; Schema: public; Owner: hil
--

CREATE SEQUENCE vlan_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;



--
-- Name: vlan_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: hil
--

ALTER SEQUENCE vlan_id_seq OWNED BY vlan.id;


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY headnode ALTER COLUMN id SET DEFAULT nextval('headnode_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY hnic ALTER COLUMN id SET DEFAULT nextval('hnic_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY metadata ALTER COLUMN id SET DEFAULT nextval('metadata_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network ALTER COLUMN id SET DEFAULT nextval('network_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_attachment ALTER COLUMN id SET DEFAULT nextval('network_attachment_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY networking_action ALTER COLUMN id SET DEFAULT nextval('networking_action_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nic ALTER COLUMN id SET DEFAULT nextval('nic_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY node ALTER COLUMN id SET DEFAULT nextval('node_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY obm ALTER COLUMN id SET DEFAULT nextval('obm_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY port ALTER COLUMN id SET DEFAULT nextval('port_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY project ALTER COLUMN id SET DEFAULT nextval('project_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY switch ALTER COLUMN id SET DEFAULT nextval('switch_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY "user" ALTER COLUMN id SET DEFAULT nextval('user_id_seq'::regclass);


--
-- Name: id; Type: DEFAULT; Schema: public; Owner: hil
--

ALTER TABLE ONLY vlan ALTER COLUMN id SET DEFAULT nextval('vlan_id_seq'::regclass);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO alembic_version (version_num) VALUES ('09d96bf567aa');
INSERT INTO alembic_version (version_num) VALUES ('03ae4ec647da');
INSERT INTO alembic_version (version_num) VALUES ('9089fa811a2b');
INSERT INTO alembic_version (version_num) VALUES ('655e037522d0');
INSERT INTO alembic_version (version_num) VALUES ('fa9ef2c9b67f');
INSERT INTO alembic_version (version_num) VALUES ('357bcff65fb3');
INSERT INTO alembic_version (version_num) VALUES ('96f1e8f87f85');
INSERT INTO alembic_version (version_num) VALUES ('b1b0e6d4302e');
INSERT INTO alembic_version (version_num) VALUES ('e06576b2ea9e');
INSERT INTO alembic_version (version_num) VALUES ('fcb23cd2e9b7');


--
-- Data for Name: brocade; Type: TABLE DATA; Schema: public; Owner: hil
--



--
-- Data for Name: dell_n3000; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO dell_n3000 (id, hostname, username, password, dummy_vlan) VALUES (6, 'user', 'host', 'pass', '5');
INSERT INTO brocade (id, hostname, username, password, interface_type) VALUES (7, 'user', 'host', 'pass', '5');


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
-- Data for Name: ipmi; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO ipmi (id, host, "user", password) VALUES (2, 'user', 'host', 'pass');


--
-- Data for Name: metadata; Type: TABLE DATA; Schema: public; Owner: hil
--



--
-- Name: metadata_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('metadata_id_seq', 1, false);


--
-- Data for Name: mock_obm; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO mock_obm (id, host, "user", password) VALUES (1, 'user', 'host', 'pass');


--
-- Data for Name: mock_switch; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO mock_switch (id, hostname, username, password) VALUES (1, 'user', 'host', 'pass');


--
-- Data for Name: network; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO network (id, label, owner_id, allocated, network_id) VALUES (1, 'runway_pxe', 1, true, '100');


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

INSERT INTO networking_action (id, type, nic_id, new_network_id, channel) VALUES (1, 'modify_port', 1, 1, 'vlan/100');
INSERT INTO networking_action (id, type, nic_id, new_network_id, channel) VALUES (2, 'modify_port', 2, 1, 'vlan/100');


--
-- Name: networking_action_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('networking_action_id_seq', 2, true);


--
-- Data for Name: nexus; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO nexus (id, hostname, username, password, dummy_vlan) VALUES (3, 'user', 'host', 'pass', '4');


--
-- Data for Name: nic; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (1, 'pxe', 1, 'de:ad:be:ef:20:17', 1);
INSERT INTO nic (id, label, owner_id, mac_addr, port_id) VALUES (2, 'pxe-dell', 2, 'be:ad:be:ef:20:18', 2);


--
-- Name: nic_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('nic_id_seq', 2, true);


--
-- Data for Name: node; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO node (id, label, project_id, obm_id) VALUES (1, 'node-1', 1, 1);
INSERT INTO node (id, label, project_id, obm_id) VALUES (2, 'node-2', 1, 2);


--
-- Name: node_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('node_id_seq', 2, true);


--
-- Data for Name: obm; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO obm (id, type) VALUES (1, 'http://schema.massopencloud.org/haas/v0/obm/mock');
INSERT INTO obm (id, type) VALUES (2, 'http://schema.massopencloud.org/haas/v0/obm/ipmi');


--
-- Name: obm_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('obm_id_seq', 2, true);


--
-- Data for Name: port; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO port (id, label, owner_id) VALUES (1, 'gi1/0/4', 1);
INSERT INTO port (id, label, owner_id) VALUES (2, 'gi1/0/5', 2);


--
-- Name: port_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('port_id_seq', 2, true);


--
-- Data for Name: power_connect55xx; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO power_connect55xx (id, hostname, username, password) VALUES (2, 'user', 'host', 'pass');


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
INSERT INTO switch (id, label, type) VALUES (2, 'sw-dell', 'http://schema.massopencloud.org/haas/v0/switches/powerconnect55xx');
INSERT INTO switch (id, label, type) VALUES (3, 'sw-nexus', 'http://schema.massopencloud.org/haas/v0/switches/nexus');
INSERT INTO switch (id, label, type) VALUES (6, 'sw-n3000', 'http://schema.massopencloud.org/haas/v0/switches/delln3000');
INSERT INTO switch (id, label, type) VALUES (7, 'sw-brocade', 'http://schema.massopencloud.org/haas/v0/switches/brocade');


--
-- Name: switch_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('switch_id_seq', 5, true);


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO "user" (id, label, is_admin, hashed_password) VALUES (1, 'ian', true, '$6$rounds=656000$iTyrApYTUhMx4b4g$YcaMExVYtS0ut2yXWrT64OggFpE4lLg12QsAuyMA3YKX6CzthXeisA47dJZW9GwU2q2CTIVrsbpxAVT64Pih2/');


--
-- Name: user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('user_id_seq', 1, true);


--
-- Data for Name: user_projects; Type: TABLE DATA; Schema: public; Owner: hil
--



--
-- Data for Name: vlan; Type: TABLE DATA; Schema: public; Owner: hil
--

INSERT INTO vlan (id, vlan_no, available) VALUES (2, 101, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (3, 102, true);
INSERT INTO vlan (id, vlan_no, available) VALUES (4, 103, true);
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


--
-- Name: vlan_id_seq; Type: SEQUENCE SET; Schema: public; Owner: hil
--

SELECT pg_catalog.setval('vlan_id_seq', 302, true);


--
-- Name: brocade_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY brocade
    ADD CONSTRAINT brocade_pkey PRIMARY KEY (id);


--
-- Name: dell_n3000_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY dell_n3000
    ADD CONSTRAINT dell_n3000_pkey PRIMARY KEY (id);


--
-- Name: headnode_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_pkey PRIMARY KEY (id);


--
-- Name: headnode_uuid_key; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_uuid_key UNIQUE (uuid);


--
-- Name: hnic_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_pkey PRIMARY KEY (id);


--
-- Name: ipmi_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY ipmi
    ADD CONSTRAINT ipmi_pkey PRIMARY KEY (id);


--
-- Name: metadata_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_pkey PRIMARY KEY (id);


--
-- Name: mock_obm_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY mock_obm
    ADD CONSTRAINT mock_obm_pkey PRIMARY KEY (id);


--
-- Name: mock_switch_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY mock_switch
    ADD CONSTRAINT mock_switch_pkey PRIMARY KEY (id);


--
-- Name: network_attachment_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_pkey PRIMARY KEY (id);


--
-- Name: network_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_pkey PRIMARY KEY (id);


--
-- Name: networking_action_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_pkey PRIMARY KEY (id);


--
-- Name: nexus_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nexus
    ADD CONSTRAINT nexus_pkey PRIMARY KEY (id);


--
-- Name: nic_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_pkey PRIMARY KEY (id);


--
-- Name: node_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_pkey PRIMARY KEY (id);


--
-- Name: obm_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY obm
    ADD CONSTRAINT obm_pkey PRIMARY KEY (id);


--
-- Name: port_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY port
    ADD CONSTRAINT port_pkey PRIMARY KEY (id);


--
-- Name: power_connect55xx_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY power_connect55xx
    ADD CONSTRAINT power_connect55xx_pkey PRIMARY KEY (id);


--
-- Name: project_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: switch_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY switch
    ADD CONSTRAINT switch_pkey PRIMARY KEY (id);


--
-- Name: user_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);


--
-- Name: vlan_pkey; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY vlan
    ADD CONSTRAINT vlan_pkey PRIMARY KEY (id);


--
-- Name: vlan_vlan_no_key; Type: CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY vlan
    ADD CONSTRAINT vlan_vlan_no_key UNIQUE (vlan_no);


--
-- Name: brocade_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY brocade
    ADD CONSTRAINT brocade_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: dell_n3000_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY dell_n3000
    ADD CONSTRAINT dell_n3000_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: headnode_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY headnode
    ADD CONSTRAINT headnode_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: hnic_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: hnic_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY hnic
    ADD CONSTRAINT hnic_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES headnode(id);


--
-- Name: ipmi_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY ipmi
    ADD CONSTRAINT ipmi_id_fkey FOREIGN KEY (id) REFERENCES obm(id);


--
-- Name: metadata_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY metadata
    ADD CONSTRAINT metadata_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES node(id);


--
-- Name: mock_obm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY mock_obm
    ADD CONSTRAINT mock_obm_id_fkey FOREIGN KEY (id) REFERENCES obm(id);


--
-- Name: mock_switch_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY mock_switch
    ADD CONSTRAINT mock_switch_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: network_attachment_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: network_attachment_nic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_attachment
    ADD CONSTRAINT network_attachment_nic_id_fkey FOREIGN KEY (nic_id) REFERENCES nic(id);


--
-- Name: network_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network
    ADD CONSTRAINT network_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES project(id);


--
-- Name: network_projects_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_projects
    ADD CONSTRAINT network_projects_network_id_fkey FOREIGN KEY (network_id) REFERENCES network(id);


--
-- Name: network_projects_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY network_projects
    ADD CONSTRAINT network_projects_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: networking_action_new_network_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_new_network_id_fkey FOREIGN KEY (new_network_id) REFERENCES network(id);


--
-- Name: networking_action_nic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY networking_action
    ADD CONSTRAINT networking_action_nic_id_fkey FOREIGN KEY (nic_id) REFERENCES nic(id);


--
-- Name: nexus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nexus
    ADD CONSTRAINT nexus_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: nic_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES node(id);


--
-- Name: nic_port_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY nic
    ADD CONSTRAINT nic_port_id_fkey FOREIGN KEY (port_id) REFERENCES port(id);


--
-- Name: node_obm_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_obm_id_fkey FOREIGN KEY (obm_id) REFERENCES obm(id);


--
-- Name: node_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY node
    ADD CONSTRAINT node_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: port_owner_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY port
    ADD CONSTRAINT port_owner_id_fkey FOREIGN KEY (owner_id) REFERENCES switch(id);


--
-- Name: power_connect55xx_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY power_connect55xx
    ADD CONSTRAINT power_connect55xx_id_fkey FOREIGN KEY (id) REFERENCES switch(id);


--
-- Name: user_projects_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY user_projects
    ADD CONSTRAINT user_projects_project_id_fkey FOREIGN KEY (project_id) REFERENCES project(id);


--
-- Name: user_projects_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: hil
--

ALTER TABLE ONLY user_projects
    ADD CONSTRAINT user_projects_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--


--
-- PostgreSQL database dump complete
--

