package de.dkrz.handlereverselookupservlet;

import java.sql.SQLException;
import java.util.Map;

import jakarta.jws.soap.SOAPBinding.Use;
import javax.servlet.ServletContext;
import javax.sql.DataSource;

import org.apache.solr.client.solrj.impl.CloudSolrClient;
import com.mchange.v2.c3p0.ComboPooledDataSource;
import com.mchange.v2.c3p0.DataSources;

/**
 * A singleton holding configuration information for the reverse lookup service.
 * This singleton is initialized once at servlet startup and persists over
 * multiple sessions that invoke the HandleReverseLookupResource. <br/>
 * 
 * The singleton also holds the connection instances to talk to the Solr and/or
 * SQL backends.
 * 
 */
public class ReverseLookupConfig {

	private static ReverseLookupConfig instance = null;

	private String jdbcDriverClassName;
	private String sqlConnectionString;
	private String sqlUsername;
	private String sqlPassword;
	private DataSource handleDataSource;

	private boolean useSolr = false;
	private boolean useSql = false;

	private String solrCloudZkHost;
	private String solrCollection;

	private CloudSolrClient solrClient;
	
	private boolean logAllQueries = false;
	private String serviceName;

	private static String getParam(ServletContext sc, Map<Object, Object> additionalProperties, Object key,
			boolean requiredParam) throws InvalidConfigException {
		String s = sc.getInitParameter(key.toString());
		if (s == null) {
			Object x = additionalProperties.get(key);
			if (x != null)
				s = x.toString();
		}
		if (requiredParam && (s == null)) {
			throw new InvalidConfigException("The configuration must specify parameter '" + key + "'!");
		}
		return s;
	}

	private static boolean getBooleanParam(ServletContext sc, Map<Object, Object> additionalProperties, Object key,
			boolean requiredParam) throws InvalidConfigException {
		if (sc.getInitParameter(key.toString()) == null) {
			Object x = additionalProperties.get(key);
			if (x != null)
				return Boolean.parseBoolean(x.toString());
			else if (requiredParam)
				throw new InvalidConfigException("The configuration must specify parameter '" + key + "'!");
		}
		return Boolean.parseBoolean(sc.getInitParameter(key.toString()));
	}

	/**
	 * Constructor that initializes the config with parameters from the servlet
	 * context and additional properties. The servlet context parameters are
	 * prioritized over the additional params.
	 * 
	 * @param servletContext
	 *            The servlet context is used to retrieve Servlet Init params;
	 *            these can be configured via web-xml, but also in e.g. Tomcat's
	 *            context.xml file.
	 * @param additionalProperties
	 *            Additional properties, typically read from a properties file.
	 * @throws InvalidConfigException
	 */
	public ReverseLookupConfig(ServletContext servletContext, Map<Object, Object> additionalProperties)
			throws InvalidConfigException {
		super();
		if (this.instance != null)
			throw new IllegalStateException("Cannot instantiate singleton more than once");
		this.useSql = getBooleanParam(servletContext, additionalProperties, "useSql", false);
		this.useSolr = getBooleanParam(servletContext, additionalProperties, "useSolr", false);
		if (useSql) {
			this.jdbcDriverClassName = getParam(servletContext, additionalProperties, "jdbcDriverClassName", true);
			this.sqlConnectionString = getParam(servletContext, additionalProperties, "sqlConnectionString", true);
			this.sqlUsername = getParam(servletContext, additionalProperties, "sqlUsername", true);
			this.sqlPassword = getParam(servletContext, additionalProperties, "sqlPassword", true);
		}
		if (useSolr) {
			this.solrCloudZkHost = getParam(servletContext, additionalProperties, "solrCloudZkHost", true);
			this.solrCollection = getParam(servletContext, additionalProperties, "solrCollection", true);
		}
		if (!(this.useSql || this.useSolr))
			throw new InvalidConfigException("The configuration must enable at least one of 'useSolr' or 'useSql'!");
		this.logAllQueries = getBooleanParam(servletContext, additionalProperties, "logAllQueries", false);
		this.serviceName = getParam(servletContext, additionalProperties, "serviceName", false);
		this.instance = this;
	}

	/**
	 * Get the singleton instance, which must have been initialized before.
	 * 
	 * @return
	 */
	public static ReverseLookupConfig getInstance() {
		return instance;
	}

	public String getJdbcDriverClassName() {
		return jdbcDriverClassName;
	}

	/**
	 * Returns the DataSource instance to use for SQL queries.
	 * 
	 * @return DataSource May be null if no SQL backend is available; call
	 *         {@link useSql} to confirm first.
	 */
	public DataSource getHandleDataSource() {
		return handleDataSource;
	}

	/**
	 * Creates a SQL data source that can afterwards be retrieved
	 * via {@link getHandleDataSource}. Only call this method once after
	 * Singleton initialization.
	 * 
	 * @throws ClassNotFoundException
	 * @throws SQLException 
	 */
	public void createHandleDataSource() throws ClassNotFoundException, SQLException {
		if (!useSql)
			return;
		/*
		 * Load jdbc driver class - this is apparently NOT done automatically
		 * for some combinations of driver, tomcat and Java
		 */
		if ((getJdbcDriverClassName() != null) && (getJdbcDriverClassName().length() > 0))
			Class.forName(getJdbcDriverClassName());
		// Create unpooled datasource, then put a pooled one on top of it
		// (done as described in c3p0 introcuction)
		DataSource ds_unpooled = DataSources.unpooledDataSource(sqlConnectionString, sqlUsername, sqlPassword);
		handleDataSource = DataSources.pooledDataSource(ds_unpooled);
	}

	/**
	 * Creates a new {@link CloudSolrClient} instance to use during the servlet
	 * lifetime. The corresponding config options must have been provided.
	 * 
	 */
	public void createSolrClient() {
		if (!useSolr)
			return;
		solrClient = new CloudSolrClient(solrCloudZkHost);
		solrClient.setDefaultCollection(solrCollection);
	}

	/**
	 * Return the {@link CloudSolrClient} instance to use (if configured).
	 * 
	 * @return {@link CloudSolrClient} May be null if no Solr backend has been
	 *         configured. Check with {@link useSolr} first.
	 */
	public CloudSolrClient getSolrClient() {
		return solrClient;
	}

	/**
	 * Confirm whether a SQL backend has been configured.
	 * 
	 * @return true if a SQL backend is available.
	 */
	public boolean useSql() {
		return useSql;
	}

	/**
	 * Confirm whether a Solr backend has been configured.
	 * 
	 * @return true if a Solr backend is available.
	 */
	public boolean useSolr() {
		return useSolr;
	}
	
	/**
	 * Queries config param to set to true optionally to log all queries with log4j. 
	 * 
	 * @return true if all requests should be logged
	 */
	public boolean isLogAllQueries() {
		return logAllQueries;
	}
	
	/**
	 * 
	 * @return A freely defined service name given by the administrator.
	 */
	public String getServiceName() {
		return serviceName;
	}

}
