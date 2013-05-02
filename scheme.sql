--
-- PostgreSQL database dump
--

SET client_encoding = 'UTF8';
SET standard_conforming_strings = off;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET escape_string_warning = off;

SET search_path = public, pg_catalog;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: access_record; Type: TABLE; Schema: public; Owner: sumin_proxybank; Tablespace: 
--

CREATE TABLE access_record (
    id uuid NOT NULL,
    proxy_id uuid NOT NULL,
    "timestamp" timestamp with time zone NOT NULL,
    user_agent character varying(255),
    remote_address character varying(64),
    alive boolean NOT NULL,
    access_time double precision,
    status_code smallint
);


ALTER TABLE public.access_record OWNER TO sumin_proxybank;

--
-- Name: proxy; Type: TABLE; Schema: public; Owner: sumin_proxybank; Tablespace: 
--

CREATE TABLE proxy (
    id uuid NOT NULL,
    protocol character varying(8) NOT NULL,
    host character varying(255) NOT NULL,
    port smallint NOT NULL,
    hit_ratio double precision,
    access_time double precision,
    last_updated timestamp with time zone
);


ALTER TABLE public.proxy OWNER TO sumin_proxybank;

--
-- Name: access_record_pkey; Type: CONSTRAINT; Schema: public; Owner: sumin_proxybank; Tablespace: 
--

ALTER TABLE ONLY access_record
    ADD CONSTRAINT access_record_pkey PRIMARY KEY (id);


--
-- Name: proxy_pkey; Type: CONSTRAINT; Schema: public; Owner: sumin_proxybank; Tablespace: 
--

ALTER TABLE ONLY proxy
    ADD CONSTRAINT proxy_pkey PRIMARY KEY (id);


--
-- Name: uri; Type: INDEX; Schema: public; Owner: sumin_proxybank; Tablespace: 
--

CREATE UNIQUE INDEX uri ON proxy USING btree (protocol, host, port);


--
-- Name: public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE ALL ON SCHEMA public FROM PUBLIC;
REVOKE ALL ON SCHEMA public FROM postgres;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;
GRANT ALL ON SCHEMA public TO sumin_proxybank;


--
-- PostgreSQL database dump complete
--
