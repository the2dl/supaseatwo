--
-- PostgreSQL database dump
--

-- Dumped from database version 15.1 (Ubuntu 15.1-1.pgdg20.04+1)
-- Dumped by pg_dump version 16.3

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
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
-- Name: downloads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.downloads (
    id bigint NOT NULL,
    hostname character varying(255) NOT NULL,
    local_path text NOT NULL,
    remote_path text NOT NULL,
    file_url text NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    status character varying(50) DEFAULT 'pending'::character varying,
    username text,
    agent_id uuid
);


ALTER TABLE public.downloads OWNER TO postgres;

--
-- Name: downloads_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.downloads_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.downloads_id_seq OWNER TO postgres;

--
-- Name: downloads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.downloads_id_seq OWNED BY public.downloads.id;


--
-- Name: file_chunks; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.file_chunks (
    id bigint NOT NULL,
    file_id uuid NOT NULL,
    file_name text NOT NULL,
    chunk_urls text[] NOT NULL,
    total_chunks integer NOT NULL,
    status text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.file_chunks OWNER TO postgres;

--
-- Name: file_chunks_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.file_chunks ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.file_chunks_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: py2; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.py2 (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    command text NOT NULL,
    status text DEFAULT 'Pending'::text NOT NULL,
    output text,
    hostname text NOT NULL,
    ip text,
    os text,
    timeout_interval bigint DEFAULT '30'::bigint,
    username text,
    smbhost text,
    ai_summary text,
    agent_id uuid
);


ALTER TABLE public.py2 OWNER TO postgres;

--
-- Name: settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.settings (
    hostname text NOT NULL,
    ip text NOT NULL,
    os text NOT NULL,
    timeout_interval integer DEFAULT 30,
    check_in text DEFAULT 'Checked-in'::text,
    last_checked_in timestamp without time zone,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    username text,
    external_ip text,
    agent_id uuid NOT NULL,
    encryption_key text,
    localuser text
);


ALTER TABLE public.settings OWNER TO postgres;

--
-- Name: uploads; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.uploads (
    hostname character varying(255) NOT NULL,
    local_path text NOT NULL,
    remote_path text NOT NULL,
    file_url text NOT NULL,
    "timestamp" timestamp with time zone DEFAULT now(),
    status character varying(50) DEFAULT 'pending'::character varying,
    username text,
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    agent_id uuid
);


ALTER TABLE public.uploads OWNER TO postgres;

--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    last_loggedin timestamp with time zone,
    last_login timestamp without time zone
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: downloads id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.downloads ALTER COLUMN id SET DEFAULT nextval('public.downloads_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: downloads downloads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.downloads
    ADD CONSTRAINT downloads_pkey PRIMARY KEY (id);


--
-- Name: file_chunks file_chunks_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.file_chunks
    ADD CONSTRAINT file_chunks_pkey PRIMARY KEY (id);


--
-- Name: py2 py2_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.py2
    ADD CONSTRAINT py2_pkey PRIMARY KEY (id);


--
-- Name: settings settings_agent_id_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_agent_id_unique UNIQUE (agent_id);


--
-- Name: settings settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.settings
    ADD CONSTRAINT settings_pkey PRIMARY KEY (id);


--
-- Name: uploads uploads_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.uploads
    ADD CONSTRAINT uploads_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: TABLE downloads; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.downloads TO anon;
GRANT ALL ON TABLE public.downloads TO authenticated;
GRANT ALL ON TABLE public.downloads TO service_role;


--
-- Name: SEQUENCE downloads_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.downloads_id_seq TO anon;
GRANT ALL ON SEQUENCE public.downloads_id_seq TO authenticated;
GRANT ALL ON SEQUENCE public.downloads_id_seq TO service_role;


--
-- Name: TABLE file_chunks; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.file_chunks TO anon;
GRANT ALL ON TABLE public.file_chunks TO authenticated;
GRANT ALL ON TABLE public.file_chunks TO service_role;


--
-- Name: SEQUENCE file_chunks_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.file_chunks_id_seq TO anon;
GRANT ALL ON SEQUENCE public.file_chunks_id_seq TO authenticated;
GRANT ALL ON SEQUENCE public.file_chunks_id_seq TO service_role;


--
-- Name: TABLE py2; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.py2 TO anon;
GRANT ALL ON TABLE public.py2 TO authenticated;
GRANT ALL ON TABLE public.py2 TO service_role;


--
-- Name: TABLE settings; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.settings TO anon;
GRANT ALL ON TABLE public.settings TO authenticated;
GRANT ALL ON TABLE public.settings TO service_role;


--
-- Name: TABLE uploads; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.uploads TO anon;
GRANT ALL ON TABLE public.uploads TO authenticated;
GRANT ALL ON TABLE public.uploads TO service_role;


--
-- Name: TABLE users; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON TABLE public.users TO anon;
GRANT ALL ON TABLE public.users TO authenticated;
GRANT ALL ON TABLE public.users TO service_role;


--
-- Name: SEQUENCE users_id_seq; Type: ACL; Schema: public; Owner: postgres
--

GRANT ALL ON SEQUENCE public.users_id_seq TO anon;
GRANT ALL ON SEQUENCE public.users_id_seq TO authenticated;
GRANT ALL ON SEQUENCE public.users_id_seq TO service_role;


--
-- PostgreSQL database dump complete
--

