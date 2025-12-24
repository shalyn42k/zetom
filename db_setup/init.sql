--
-- PostgreSQL database dump
--

\restrict gmFPfWCjXETOT5tRN2RtyYCnpHBP7mhZMuRbDHcrADcNOcdQ4JPYMH26S0cPEJf

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

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

ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_user_id_c564eba6_fk_auth_user_id;
ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_content_type_id_c4bce8eb_fk_django_co;
ALTER TABLE IF EXISTS ONLY public.contact_contactattachment DROP CONSTRAINT IF EXISTS contact_contactattac_message_id_1c7ae848_fk_contact_c;
ALTER TABLE IF EXISTS ONLY public.contact_clientchangelog DROP CONSTRAINT IF EXISTS contact_clientchange_message_id_9d95fc77_fk_contact_c;
ALTER TABLE IF EXISTS ONLY public.contact_adminuser_departments DROP CONSTRAINT IF EXISTS contact_adminuser_de_department_id_add7ba45_fk_contact_d;
ALTER TABLE IF EXISTS ONLY public.contact_adminuser_departments DROP CONSTRAINT IF EXISTS contact_adminuser_de_adminuser_id_e8ba32ed_fk_contact_a;
ALTER TABLE IF EXISTS ONLY public.contact_adminactivitylog DROP CONSTRAINT IF EXISTS contact_adminactivit_message_id_4e876a5d_fk_contact_c;
ALTER TABLE IF EXISTS ONLY public.auth_user_user_permissions DROP CONSTRAINT IF EXISTS auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id;
ALTER TABLE IF EXISTS ONLY public.auth_user_user_permissions DROP CONSTRAINT IF EXISTS auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm;
ALTER TABLE IF EXISTS ONLY public.auth_user_groups DROP CONSTRAINT IF EXISTS auth_user_groups_user_id_6a12ed8b_fk_auth_user_id;
ALTER TABLE IF EXISTS ONLY public.auth_user_groups DROP CONSTRAINT IF EXISTS auth_user_groups_group_id_97559544_fk_auth_group_id;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_content_type_id_2f476e4b_fk_django_co;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_group_id_b120cbf9_fk_auth_group_id;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissio_permission_id_84c5c92e_fk_auth_perm;
DROP INDEX IF EXISTS public.django_session_session_key_c0390e0f_like;
DROP INDEX IF EXISTS public.django_session_expire_date_a5c62663;
DROP INDEX IF EXISTS public.django_admin_log_user_id_c564eba6;
DROP INDEX IF EXISTS public.django_admin_log_content_type_id_c4bce8eb;
DROP INDEX IF EXISTS public.contact_department_code_b5e7606e_like;
DROP INDEX IF EXISTS public.contact_contactmessage_status_fe7e79d6_like;
DROP INDEX IF EXISTS public.contact_contactmessage_status_fe7e79d6;
DROP INDEX IF EXISTS public.contact_contactmessage_is_deleted_15bd733c;
DROP INDEX IF EXISTS public.contact_contactmessage_created_at_0ef56624;
DROP INDEX IF EXISTS public.contact_contactmessage_company_8b57dd5f_like;
DROP INDEX IF EXISTS public.contact_contactmessage_company_8b57dd5f;
DROP INDEX IF EXISTS public.contact_contactattachment_message_id_1c7ae848;
DROP INDEX IF EXISTS public.contact_clientchangelog_message_id_9d95fc77;
DROP INDEX IF EXISTS public.contact_clientchangelog_is_reverted_f9dbdb86;
DROP INDEX IF EXISTS public.contact_clientchangelog_changed_at_72ee6dd1;
DROP INDEX IF EXISTS public.contact_adminuser_email_0bdd6554_like;
DROP INDEX IF EXISTS public.contact_adminuser_departments_department_id_add7ba45;
DROP INDEX IF EXISTS public.contact_adminuser_departments_adminuser_id_e8ba32ed;
DROP INDEX IF EXISTS public.contact_adminuser_created_at_d2d81314;
DROP INDEX IF EXISTS public.contact_adminactivitylog_message_id_4e876a5d;
DROP INDEX IF EXISTS public.contact_adminactivitylog_created_at_24a2ae0a;
DROP INDEX IF EXISTS public.auth_user_username_6821ab7c_like;
DROP INDEX IF EXISTS public.auth_user_user_permissions_user_id_a95ead1b;
DROP INDEX IF EXISTS public.auth_user_user_permissions_permission_id_1fbb5f2c;
DROP INDEX IF EXISTS public.auth_user_groups_user_id_6a12ed8b;
DROP INDEX IF EXISTS public.auth_user_groups_group_id_97559544;
DROP INDEX IF EXISTS public.auth_permission_content_type_id_2f476e4b;
DROP INDEX IF EXISTS public.auth_group_permissions_permission_id_84c5c92e;
DROP INDEX IF EXISTS public.auth_group_permissions_group_id_b120cbf9;
DROP INDEX IF EXISTS public.auth_group_name_a6ea08ec_like;
ALTER TABLE IF EXISTS ONLY public.django_session DROP CONSTRAINT IF EXISTS django_session_pkey;
ALTER TABLE IF EXISTS ONLY public.django_migrations DROP CONSTRAINT IF EXISTS django_migrations_pkey;
ALTER TABLE IF EXISTS ONLY public.django_content_type DROP CONSTRAINT IF EXISTS django_content_type_pkey;
ALTER TABLE IF EXISTS ONLY public.django_content_type DROP CONSTRAINT IF EXISTS django_content_type_app_label_model_76bd3d3b_uniq;
ALTER TABLE IF EXISTS ONLY public.django_admin_log DROP CONSTRAINT IF EXISTS django_admin_log_pkey;
ALTER TABLE IF EXISTS ONLY public.contact_department DROP CONSTRAINT IF EXISTS contact_department_pkey;
ALTER TABLE IF EXISTS ONLY public.contact_department DROP CONSTRAINT IF EXISTS contact_department_code_key;
ALTER TABLE IF EXISTS ONLY public.contact_contactmessage DROP CONSTRAINT IF EXISTS contact_contactmessage_pkey;
ALTER TABLE IF EXISTS ONLY public.contact_contactattachment DROP CONSTRAINT IF EXISTS contact_contactattachment_pkey;
ALTER TABLE IF EXISTS ONLY public.contact_clientchangelog DROP CONSTRAINT IF EXISTS contact_clientchangelog_pkey;
ALTER TABLE IF EXISTS ONLY public.contact_adminuser DROP CONSTRAINT IF EXISTS contact_adminuser_pkey;
ALTER TABLE IF EXISTS ONLY public.contact_adminuser DROP CONSTRAINT IF EXISTS contact_adminuser_email_key;
ALTER TABLE IF EXISTS ONLY public.contact_adminuser_departments DROP CONSTRAINT IF EXISTS contact_adminuser_departments_pkey;
ALTER TABLE IF EXISTS ONLY public.contact_adminuser_departments DROP CONSTRAINT IF EXISTS contact_adminuser_depart_adminuser_id_department__2ca296e2_uniq;
ALTER TABLE IF EXISTS ONLY public.contact_adminactivitylog DROP CONSTRAINT IF EXISTS contact_adminactivitylog_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_user DROP CONSTRAINT IF EXISTS auth_user_username_key;
ALTER TABLE IF EXISTS ONLY public.auth_user_user_permissions DROP CONSTRAINT IF EXISTS auth_user_user_permissions_user_id_permission_id_14a6b632_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_user_user_permissions DROP CONSTRAINT IF EXISTS auth_user_user_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_user DROP CONSTRAINT IF EXISTS auth_user_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_user_groups DROP CONSTRAINT IF EXISTS auth_user_groups_user_id_group_id_94350c0c_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_user_groups DROP CONSTRAINT IF EXISTS auth_user_groups_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_permission DROP CONSTRAINT IF EXISTS auth_permission_content_type_id_codename_01ab375a_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_group DROP CONSTRAINT IF EXISTS auth_group_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.auth_group_permissions DROP CONSTRAINT IF EXISTS auth_group_permissions_group_id_permission_id_0cd325b0_uniq;
ALTER TABLE IF EXISTS ONLY public.auth_group DROP CONSTRAINT IF EXISTS auth_group_name_key;
DROP TABLE IF EXISTS public.django_session;
DROP TABLE IF EXISTS public.django_migrations;
DROP TABLE IF EXISTS public.django_content_type;
DROP TABLE IF EXISTS public.django_admin_log;
DROP TABLE IF EXISTS public.contact_department;
DROP TABLE IF EXISTS public.contact_contactmessage;
DROP TABLE IF EXISTS public.contact_contactattachment;
DROP TABLE IF EXISTS public.contact_clientchangelog;
DROP TABLE IF EXISTS public.contact_adminuser_departments;
DROP TABLE IF EXISTS public.contact_adminuser;
DROP TABLE IF EXISTS public.contact_adminactivitylog;
DROP TABLE IF EXISTS public.auth_user_user_permissions;
DROP TABLE IF EXISTS public.auth_user_groups;
DROP TABLE IF EXISTS public.auth_user;
DROP TABLE IF EXISTS public.auth_permission;
DROP TABLE IF EXISTS public.auth_group_permissions;
DROP TABLE IF EXISTS public.auth_group;
-- *not* dropping schema, since initdb creates it
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: zetom_user
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO zetom_user;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO zetom_user;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO zetom_user;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO zetom_user;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO zetom_user;

--
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO zetom_user;

--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.auth_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.auth_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO zetom_user;

--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: contact_adminactivitylog; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.contact_adminactivitylog (
    id bigint NOT NULL,
    action character varying(32) NOT NULL,
    description text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    message_id bigint
);


ALTER TABLE public.contact_adminactivitylog OWNER TO zetom_user;

--
-- Name: contact_adminactivitylog_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.contact_adminactivitylog ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.contact_adminactivitylog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: contact_adminuser; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.contact_adminuser (
    id bigint NOT NULL,
    email character varying(254) NOT NULL,
    password_hash character varying(128) NOT NULL,
    created_at timestamp with time zone NOT NULL,
    updated_at timestamp with time zone NOT NULL,
    level_of_access character varying(20) NOT NULL,
    last_password_reset_at timestamp with time zone,
    permissions_override jsonb NOT NULL
);


ALTER TABLE public.contact_adminuser OWNER TO zetom_user;

--
-- Name: contact_adminuser_departments; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.contact_adminuser_departments (
    id bigint NOT NULL,
    adminuser_id bigint NOT NULL,
    department_id bigint NOT NULL
);


ALTER TABLE public.contact_adminuser_departments OWNER TO zetom_user;

--
-- Name: contact_adminuser_departments_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.contact_adminuser_departments ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.contact_adminuser_departments_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: contact_adminuser_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.contact_adminuser ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.contact_adminuser_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: contact_clientchangelog; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.contact_clientchangelog (
    id bigint NOT NULL,
    field character varying(32) NOT NULL,
    previous_value text NOT NULL,
    new_value text NOT NULL,
    changed_at timestamp with time zone NOT NULL,
    is_reverted boolean NOT NULL,
    message_id bigint NOT NULL
);


ALTER TABLE public.contact_clientchangelog OWNER TO zetom_user;

--
-- Name: contact_clientchangelog_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.contact_clientchangelog ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.contact_clientchangelog_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: contact_contactattachment; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.contact_contactattachment (
    id bigint NOT NULL,
    file character varying(100) NOT NULL,
    original_name character varying(255) NOT NULL,
    content_type character varying(255) NOT NULL,
    size integer NOT NULL,
    uploaded_at timestamp with time zone NOT NULL,
    message_id bigint NOT NULL,
    CONSTRAINT contact_contactattachment_size_check CHECK ((size >= 0))
);


ALTER TABLE public.contact_contactattachment OWNER TO zetom_user;

--
-- Name: contact_contactattachment_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.contact_contactattachment ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.contact_contactattachment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: contact_contactmessage; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.contact_contactmessage (
    id bigint NOT NULL,
    phone character varying(20) NOT NULL,
    email character varying(254) NOT NULL,
    company character varying(50) NOT NULL,
    message text NOT NULL,
    created_at timestamp with time zone NOT NULL,
    status character varying(32) NOT NULL,
    is_deleted boolean NOT NULL,
    final_changes text NOT NULL,
    final_response text NOT NULL,
    access_enabled boolean NOT NULL,
    access_token_hash character varying(128) NOT NULL,
    access_token_expires_at timestamp with time zone,
    full_name character varying(200) NOT NULL,
    company_name character varying(150) NOT NULL
);


ALTER TABLE public.contact_contactmessage OWNER TO zetom_user;

--
-- Name: contact_contactmessage_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.contact_contactmessage ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.contact_contactmessage_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: contact_department; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.contact_department (
    id bigint NOT NULL,
    code character varying(50) NOT NULL,
    name_pl character varying(100) NOT NULL,
    name_en character varying(100) NOT NULL
);


ALTER TABLE public.contact_department OWNER TO zetom_user;

--
-- Name: contact_department_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.contact_department ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.contact_department_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO zetom_user;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO zetom_user;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO zetom_user;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: zetom_user
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: zetom_user
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO zetom_user;

--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add user	4	add_user
14	Can change user	4	change_user
15	Can delete user	4	delete_user
16	Can view user	4	view_user
17	Can add content type	5	add_contenttype
18	Can change content type	5	change_contenttype
19	Can delete content type	5	delete_contenttype
20	Can view content type	5	view_contenttype
21	Can add session	6	add_session
22	Can change session	6	change_session
23	Can delete session	6	delete_session
24	Can view session	6	view_session
25	Can add contact message	7	add_contactmessage
26	Can change contact message	7	change_contactmessage
27	Can delete contact message	7	delete_contactmessage
28	Can view contact message	7	view_contactmessage
29	Can add contact attachment	8	add_contactattachment
30	Can change contact attachment	8	change_contactattachment
31	Can delete contact attachment	8	delete_contactattachment
32	Can view contact attachment	8	view_contactattachment
33	Can add department	9	add_department
34	Can change department	9	change_department
35	Can delete department	9	delete_department
36	Can view department	9	view_department
37	Can add admin user	10	add_adminuser
38	Can change admin user	10	change_adminuser
39	Can delete admin user	10	delete_adminuser
40	Can view admin user	10	view_adminuser
41	Can add admin activity log	11	add_adminactivitylog
42	Can change admin activity log	11	change_adminactivitylog
43	Can delete admin activity log	11	delete_adminactivitylog
44	Can view admin activity log	11	view_adminactivitylog
45	Can add client change log	12	add_clientchangelog
46	Can change client change log	12	change_clientchangelog
47	Can delete client change log	12	delete_clientchangelog
48	Can view client change log	12	view_clientchangelog
\.


--
-- Data for Name: auth_user; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) FROM stdin;
\.


--
-- Data for Name: auth_user_groups; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.auth_user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: auth_user_user_permissions; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.auth_user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: contact_adminactivitylog; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.contact_adminactivitylog (id, action, description, created_at, message_id) FROM stdin;
1	email	Manual email sent to tymirapps@gmail.com	2025-12-24 15:41:46.57461+00	\N
2	email	Manual email sent to tymirapps@gmail.com	2025-12-28 18:02:04.597145+00	\N
\.


--
-- Data for Name: contact_adminuser; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.contact_adminuser (id, email, password_hash, created_at, updated_at, level_of_access, last_password_reset_at, permissions_override) FROM stdin;
1	test@gmail.com	pbkdf2_sha256$1000000$1ivAldwXcD8nOhLAldK2mi$WzpYLh2/W9sKAZYZZrrWw7ySZCVdXAQkP8C+5Txp6l4=	2025-12-24 15:36:56.780505+00	2025-12-24 15:36:56.883181+00	level1	\N	{}
\.


--
-- Data for Name: contact_adminuser_departments; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.contact_adminuser_departments (id, adminuser_id, department_id) FROM stdin;
\.


--
-- Data for Name: contact_clientchangelog; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.contact_clientchangelog (id, field, previous_value, new_value, changed_at, is_reverted, message_id) FROM stdin;
\.


--
-- Data for Name: contact_contactattachment; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.contact_contactattachment (id, file, original_name, content_type, size, uploaded_at, message_id) FROM stdin;
\.


--
-- Data for Name: contact_contactmessage; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.contact_contactmessage (id, phone, email, company, message, created_at, status, is_deleted, final_changes, final_response, access_enabled, access_token_hash, access_token_expires_at, full_name, company_name) FROM stdin;
1	adadad	tymirapps@gmail.com	Dlugosci i Kąta	adada	2025-12-24 16:08:05.47853+00	new	f			t	pbkdf2_sha256$1000000$s7wju87iSQ0xWXLbL6pWbD$Rc9bacJdpnM/A89pPG4V6tYLlyYedEYxB76gp0VvvFw=	2025-12-27 16:08:05.585321+00	adada	adada
\.


--
-- Data for Name: contact_department; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.contact_department (id, code, name_pl, name_en) FROM stdin;
1	Elektrotechniczne	Elektrotechniczne	Electrotechnical
2	Dlugosci i Kąta	Dlugosci i Kąta	Length and Angle
3	Mechaniczna	Mechaniczna	Mechanical
4	inne	Inne	Other
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	auth	user
5	contenttypes	contenttype
6	sessions	session
7	contact	contactmessage
8	contact	contactattachment
9	contact	department
10	contact	adminuser
11	contact	adminactivitylog
12	contact	clientchangelog
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	contenttypes	0001_initial	2025-12-16 15:44:42.444007+00
2	auth	0001_initial	2025-12-16 15:44:42.462911+00
3	admin	0001_initial	2025-12-16 15:44:42.47069+00
4	admin	0002_logentry_remove_auto_add	2025-12-16 15:44:42.476076+00
5	admin	0003_logentry_add_action_flag_choices	2025-12-16 15:44:42.479892+00
6	contenttypes	0002_remove_content_type_name	2025-12-16 15:44:42.488408+00
7	auth	0002_alter_permission_name_max_length	2025-12-16 15:44:42.493187+00
8	auth	0003_alter_user_email_max_length	2025-12-16 15:44:42.49766+00
9	auth	0004_alter_user_username_opts	2025-12-16 15:44:42.500843+00
10	auth	0005_alter_user_last_login_null	2025-12-16 15:44:42.505138+00
11	auth	0006_require_contenttypes_0002	2025-12-16 15:44:42.505963+00
12	auth	0007_alter_validators_add_error_messages	2025-12-16 15:44:42.511723+00
13	auth	0008_alter_user_username_max_length	2025-12-16 15:44:42.517364+00
14	auth	0009_alter_user_last_name_max_length	2025-12-16 15:44:42.520951+00
15	auth	0010_alter_group_name_max_length	2025-12-16 15:44:42.524522+00
16	auth	0011_update_proxy_permissions	2025-12-16 15:44:42.527804+00
17	auth	0012_alter_user_first_name_max_length	2025-12-16 15:44:42.530885+00
18	contact	0001_initial	2025-12-16 15:44:42.534691+00
19	contact	0002_replace_is_read_with_status	2025-12-16 15:44:42.538495+00
20	contact	0003_contactmessage_is_deleted	2025-12-16 15:44:42.540537+00
21	contact	0004_contactmessage_final_changes_and_more	2025-12-16 15:44:42.543375+00
22	contact	0005_contactmessage_access_enabled_and_more	2025-12-16 15:44:42.549983+00
23	contact	0006_contactmessage_access_token_expires_at_and_more	2025-12-16 15:44:42.553302+00
24	contact	0007_rename_name_fields	2025-12-16 15:44:42.573935+00
25	contact	0008_adminuser	2025-12-16 15:44:42.576561+00
26	contact	0009_adminuser_department	2025-12-16 15:44:42.57776+00
27	contact	0010_adminuser_password_ciphertext	2025-12-16 15:44:42.579379+00
28	contact	0011_alter_adminuser_department	2025-12-16 15:44:42.580358+00
29	contact	0012_department_remove_adminuser_department_and_more	2025-12-16 15:44:42.600512+00
30	contact	0013_adminuser_last_password_reset_at	2025-12-16 15:44:42.602406+00
31	contact	0014_update_departments_values	2025-12-16 15:44:42.617015+00
32	contact	0015_adminuser_permissions_override	2025-12-16 15:44:42.619955+00
33	sessions	0001_initial	2025-12-16 15:44:42.62275+00
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: zetom_user
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
ouegmkrz7ybaymgkqpy9bdsus6wavcei	.eJwtjMsKAjEQBP-lz0HYa07-h8gwJG0I5CFJ1ov47467HrupqjeKtgQPNjjsk0Mq59REyXHC3-4OpafEKLnBr7HTQWPNTQ44R_jNEL5YpD9EQzDdesezWTPyqWNVtvXPnTar5mLc4lzX9BuX0Cs-X1g1MqY:1vZv8Z:cYNzHVm77r9n4_FGWoEMqb9teUJMldYYMMsTYcQDfuk	2025-12-28 19:05:03.890439+00
bdk4ag74c8e70ao18z9wnkq0uysxag1y	.eJw1jEsKAyEUBO_Sawm4dZV7hOHx0I4IfoI6sxly9zgDWXZTVSey1ggHVhjsg10Kx9BISWHAvexmkFuMDJIq3Ow7DTSUVOWmU4CzC-HBLO0t6v3yV_B-7IoGfrTPwjqv3va3WTTlxU2O-YzXePhW8P0BeTAy1w:1vYRSf:JDIZY4RmTMYiVH-vfw2NeajSpT3iZSGU2vcj3XRBrL8	2025-12-24 17:11:41.709085+00
tpjk4hkqqvp54x2cjxxqq24fjlmfbv0n	eyJsYW5nIjoicGwifQ:1vZYko:3qD2xxdlKF4iZuRCTizUY_Fh_o53oShOtBVK_Bn3y9c	2025-12-27 19:11:02.775214+00
\.


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 48, true);


--
-- Name: auth_user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.auth_user_groups_id_seq', 1, false);


--
-- Name: auth_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.auth_user_id_seq', 1, false);


--
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.auth_user_user_permissions_id_seq', 1, false);


--
-- Name: contact_adminactivitylog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.contact_adminactivitylog_id_seq', 2, true);


--
-- Name: contact_adminuser_departments_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.contact_adminuser_departments_id_seq', 1, false);


--
-- Name: contact_adminuser_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.contact_adminuser_id_seq', 1, true);


--
-- Name: contact_clientchangelog_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.contact_clientchangelog_id_seq', 1, false);


--
-- Name: contact_contactattachment_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.contact_contactattachment_id_seq', 1, false);


--
-- Name: contact_contactmessage_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.contact_contactmessage_id_seq', 1, true);


--
-- Name: contact_department_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.contact_department_id_seq', 4, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 12, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: zetom_user
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 33, true);


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- Name: contact_adminactivitylog contact_adminactivitylog_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_adminactivitylog
    ADD CONSTRAINT contact_adminactivitylog_pkey PRIMARY KEY (id);


--
-- Name: contact_adminuser_departments contact_adminuser_depart_adminuser_id_department__2ca296e2_uniq; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_adminuser_departments
    ADD CONSTRAINT contact_adminuser_depart_adminuser_id_department__2ca296e2_uniq UNIQUE (adminuser_id, department_id);


--
-- Name: contact_adminuser_departments contact_adminuser_departments_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_adminuser_departments
    ADD CONSTRAINT contact_adminuser_departments_pkey PRIMARY KEY (id);


--
-- Name: contact_adminuser contact_adminuser_email_key; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_adminuser
    ADD CONSTRAINT contact_adminuser_email_key UNIQUE (email);


--
-- Name: contact_adminuser contact_adminuser_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_adminuser
    ADD CONSTRAINT contact_adminuser_pkey PRIMARY KEY (id);


--
-- Name: contact_clientchangelog contact_clientchangelog_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_clientchangelog
    ADD CONSTRAINT contact_clientchangelog_pkey PRIMARY KEY (id);


--
-- Name: contact_contactattachment contact_contactattachment_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_contactattachment
    ADD CONSTRAINT contact_contactattachment_pkey PRIMARY KEY (id);


--
-- Name: contact_contactmessage contact_contactmessage_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_contactmessage
    ADD CONSTRAINT contact_contactmessage_pkey PRIMARY KEY (id);


--
-- Name: contact_department contact_department_code_key; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_department
    ADD CONSTRAINT contact_department_code_key UNIQUE (code);


--
-- Name: contact_department contact_department_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_department
    ADD CONSTRAINT contact_department_pkey PRIMARY KEY (id);


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- Name: contact_adminactivitylog_created_at_24a2ae0a; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_adminactivitylog_created_at_24a2ae0a ON public.contact_adminactivitylog USING btree (created_at);


--
-- Name: contact_adminactivitylog_message_id_4e876a5d; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_adminactivitylog_message_id_4e876a5d ON public.contact_adminactivitylog USING btree (message_id);


--
-- Name: contact_adminuser_created_at_d2d81314; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_adminuser_created_at_d2d81314 ON public.contact_adminuser USING btree (created_at);


--
-- Name: contact_adminuser_departments_adminuser_id_e8ba32ed; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_adminuser_departments_adminuser_id_e8ba32ed ON public.contact_adminuser_departments USING btree (adminuser_id);


--
-- Name: contact_adminuser_departments_department_id_add7ba45; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_adminuser_departments_department_id_add7ba45 ON public.contact_adminuser_departments USING btree (department_id);


--
-- Name: contact_adminuser_email_0bdd6554_like; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_adminuser_email_0bdd6554_like ON public.contact_adminuser USING btree (email varchar_pattern_ops);


--
-- Name: contact_clientchangelog_changed_at_72ee6dd1; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_clientchangelog_changed_at_72ee6dd1 ON public.contact_clientchangelog USING btree (changed_at);


--
-- Name: contact_clientchangelog_is_reverted_f9dbdb86; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_clientchangelog_is_reverted_f9dbdb86 ON public.contact_clientchangelog USING btree (is_reverted);


--
-- Name: contact_clientchangelog_message_id_9d95fc77; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_clientchangelog_message_id_9d95fc77 ON public.contact_clientchangelog USING btree (message_id);


--
-- Name: contact_contactattachment_message_id_1c7ae848; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_contactattachment_message_id_1c7ae848 ON public.contact_contactattachment USING btree (message_id);


--
-- Name: contact_contactmessage_company_8b57dd5f; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_contactmessage_company_8b57dd5f ON public.contact_contactmessage USING btree (company);


--
-- Name: contact_contactmessage_company_8b57dd5f_like; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_contactmessage_company_8b57dd5f_like ON public.contact_contactmessage USING btree (company varchar_pattern_ops);


--
-- Name: contact_contactmessage_created_at_0ef56624; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_contactmessage_created_at_0ef56624 ON public.contact_contactmessage USING btree (created_at);


--
-- Name: contact_contactmessage_is_deleted_15bd733c; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_contactmessage_is_deleted_15bd733c ON public.contact_contactmessage USING btree (is_deleted);


--
-- Name: contact_contactmessage_status_fe7e79d6; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_contactmessage_status_fe7e79d6 ON public.contact_contactmessage USING btree (status);


--
-- Name: contact_contactmessage_status_fe7e79d6_like; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_contactmessage_status_fe7e79d6_like ON public.contact_contactmessage USING btree (status varchar_pattern_ops);


--
-- Name: contact_department_code_b5e7606e_like; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX contact_department_code_b5e7606e_like ON public.contact_department USING btree (code varchar_pattern_ops);


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: zetom_user
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: contact_adminactivitylog contact_adminactivit_message_id_4e876a5d_fk_contact_c; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_adminactivitylog
    ADD CONSTRAINT contact_adminactivit_message_id_4e876a5d_fk_contact_c FOREIGN KEY (message_id) REFERENCES public.contact_contactmessage(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: contact_adminuser_departments contact_adminuser_de_adminuser_id_e8ba32ed_fk_contact_a; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_adminuser_departments
    ADD CONSTRAINT contact_adminuser_de_adminuser_id_e8ba32ed_fk_contact_a FOREIGN KEY (adminuser_id) REFERENCES public.contact_adminuser(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: contact_adminuser_departments contact_adminuser_de_department_id_add7ba45_fk_contact_d; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_adminuser_departments
    ADD CONSTRAINT contact_adminuser_de_department_id_add7ba45_fk_contact_d FOREIGN KEY (department_id) REFERENCES public.contact_department(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: contact_clientchangelog contact_clientchange_message_id_9d95fc77_fk_contact_c; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_clientchangelog
    ADD CONSTRAINT contact_clientchange_message_id_9d95fc77_fk_contact_c FOREIGN KEY (message_id) REFERENCES public.contact_contactmessage(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: contact_contactattachment contact_contactattac_message_id_1c7ae848_fk_contact_c; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.contact_contactattachment
    ADD CONSTRAINT contact_contactattac_message_id_1c7ae848_fk_contact_c FOREIGN KEY (message_id) REFERENCES public.contact_contactmessage(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: zetom_user
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO zetom_user;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO zetom_user;


--
-- PostgreSQL database dump complete
--

\unrestrict gmFPfWCjXETOT5tRN2RtyYCnpHBP7mhZMuRbDHcrADcNOcdQ4JPYMH26S0cPEJf

