package de.dkrz.handlereverselookupservlet;

import java.io.IOException;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;

import javax.sql.DataSource;
import javax.ws.rs.GET;
import javax.ws.rs.Path;
import javax.ws.rs.Produces;
import javax.ws.rs.core.Context;
import javax.ws.rs.core.MediaType;
import javax.ws.rs.core.MultivaluedHashMap;
import javax.ws.rs.core.MultivaluedMap;
import javax.ws.rs.core.Response;
import javax.ws.rs.core.UriInfo;

import org.apache.logging.log4j.LogManager;
import org.apache.logging.log4j.Logger;
import org.apache.solr.client.solrj.SolrQuery;
import org.apache.solr.client.solrj.SolrServerException;
import org.apache.solr.client.solrj.impl.CloudSolrClient;
import org.apache.solr.client.solrj.impl.HttpSolrClient.RemoteSolrException;
import org.apache.solr.client.solrj.response.QueryResponse;
import org.apache.solr.common.SolrDocument;
import org.apache.solr.common.SolrDocumentList;

@Path("/")
public class HandleReverseLookupResource {

	private static final Logger LOGGER = LogManager.getLogger(HandleReverseLookupResource.class);

	@GET
	@Path("ping")
	public String ping() {
		return "OK\n";
	}
	
	/**
	 * Searches over Handles via their record information. The method will return a list of all Handles whose records match all of the supplied parameters.
	 * The parameters are not a fixed set; the usual 'URL' field is a good example as this establishes what is usually understood as Handle reverse-lookup: Get to a Handle given a target URL. 
	 * However, any fields that are available from the Handle SQL storage or a Solr index can be used.
	 * 
	 * All parameters are treated as such search fields except for a few special ones:
	 * <ul>
	 * <li><em>limit:</em> Limits the maximum number of results to return. The default limit for Solr queries is 1000; there is no default for SQL. Limits for Solr larger than 1000 can be specified.</li>
	 * <li><em>page (SQL only):</em> Skip the given number of results, enabling pagination if combined with a limit. Limits the maximum number of results to return.</li>
	 * <li><em>enforcesql:</em> If both SQL and Solr are configured for searching, Solr takes precedence by default. If enforcesql is set to true, SQL will be used instead of Solr.
	 * <li><em>retrieverecords (SQL only):</em> Do not only return Handle names, but full record contents. Note: This only works if only one search field is given.</li>
	 * </dl>
	 * 
	 * @param info A UriInfo object carrying, among other things, the URL parameters. See above for explanations.
	 * @return A simple list of Handles (just Handle names, no record excerpts, even not for the fields searched).
	 */
	@GET
	@Path("handles")
	@Produces("application/json")
	public Response search(@Context UriInfo info) {
		MultivaluedMap<String, String> params = info.getQueryParameters();
		ReverseLookupConfig configuration = ReverseLookupConfig.getInstance();
		Integer limit = null;
		Integer page = null;
		boolean enforceSql = false;
		boolean retrieveRecords = false;
		MultivaluedMap<String, String> filteredParams = new MultivaluedHashMap<String, String>(params);
		try {
			if (filteredParams.containsKey("limit")) {
				limit = Integer.parseInt(filteredParams.getFirst("limit"));
				filteredParams.remove("limit");
			}
			if (filteredParams.containsKey("page")) {
				page = Integer.parseInt(filteredParams.getFirst("page"));
				filteredParams.remove("page");
			}
			if (filteredParams.containsKey("enforcesql")) {
				enforceSql = Boolean.parseBoolean(filteredParams.getFirst("enforcesql"));
				filteredParams.remove("enforcesql");
				if (enforceSql && !configuration.useSql())
					return Response.serverError()
							.entity("You asked to enforce SQL usage for searching, but this service is not configured for SQL.")
							.build();
			}
			if (filteredParams.containsKey("retrieverecords")) {
				retrieveRecords = Boolean.parseBoolean(filteredParams.getFirst("retrieverecords"));
				filteredParams.remove("retrieverecords");
			}
			Object result;
			// If available, search via solr takes precedence over SQL unless
			// enforced otherwise
			if (configuration.useSolr() && !enforceSql) {
				result = genericSolrSearch(filteredParams, limit);
			} else {
				result = genericSqlSearch(filteredParams, limit, page, retrieveRecords);
			}
			return Response.ok(result, MediaType.APPLICATION_JSON).build();
		} catch (SQLException exc) {
			LOGGER.error(exc);
			return Response.serverError()
					.entity("\"" + exc.getMessage() + " (SQL error code " + exc.getErrorCode() + "; SQL State "+exc.getSQLState()+")\"\n").build();
		} catch (IOException exc) {
			LOGGER.error(exc);
			return Response.serverError().entity("\"IOException: " + exc.getMessage() + "\"\n").build();
		} catch (NumberFormatException exc) {
			LOGGER.error(exc);
			return Response.serverError().entity("\"Invalid number: " + exc.getMessage() + "\"\n").build();
		} catch (SolrServerException exc) {
			LOGGER.error(exc);
			return Response.serverError().entity("\"SolrServerException: " + exc.getMessage() + "\"\n").build();
		} catch (RemoteSolrException exc) {
			return Response.status(Response.Status.BAD_REQUEST).entity("\"RemoteSolrException: " + exc.getMessage() + "\"\n").build();
		}
	}

	/**
	 * Searches Handles via Solr.
	 * 
	 * @param parameters A map of all search fields. Should not contain special parameters such as 'limit' or 'enforcesql'.
	 * @param limit Maximum number of results to return. May be null, in which case 1000 is the default.
	 * @return A list of Handles.
	 * @throws SolrServerException
	 * @throws IOException
	 */
	public List<String> genericSolrSearch(MultivaluedMap<String, String> parameters, Integer limit)
			throws SolrServerException, IOException {
		List<String> results = new LinkedList<String>();
		if (parameters.isEmpty()) {
			return results;
		}
		ReverseLookupConfig configuration = ReverseLookupConfig.getInstance();
		CloudSolrClient solr = configuration.getSolrClient();
		try {
			SolrQuery query = new SolrQuery();
			if (limit == null)
				query.setRows(1000);
			else
				query.setRows(limit);
			StringBuilder querysb = new StringBuilder();
			int i = 0;
			for (String key : parameters.keySet()) {
				List<String> values = parameters.get(key);
				Iterator<String> valueIter = values.iterator();
				while (valueIter.hasNext()) {
					String v = valueIter.next();
					if (i > 0)
						querysb.append(" AND ");
					querysb.append(key+":"+escapeSolrQueryChars(v));
					i++;
				}
			}
			query.add("q", querysb.toString());
			LOGGER.debug("Solr query: " + query);
			QueryResponse queryResponse = solr.query(query);
			SolrDocumentList docs = queryResponse.getResults();
			for (SolrDocument doc : docs) {
				results.add(doc.get("id").toString());
			}
		} finally {
		}
		return results;
	}

	private String escapeSolrQueryChars(String s) {
		// Taken from solrj source. Will do normal filtering except for
		// asterisks.
		StringBuilder sb = new StringBuilder();
		for (int i = 0; i < s.length(); i++) {
			char c = s.charAt(i);
			// These characters are part of the query syntax and must be escaped
			if (c == '\\' || c == '+' || c == '-' || c == '!' || c == '(' || c == ')' || c == ':' || c == '^'
					|| c == '[' || c == ']' || c == '\"' || c == '{' || c == '}' || c == '~' || c == '?' || c == '|'
					|| c == '&' || c == ';' || c == '/' || Character.isWhitespace(c)) {
				sb.append('\\');
			}
			sb.append(c);
		}
		return sb.toString();
	}

	/**
	 * Queries SQL for Handles whose type/data pairs match particular filters.
	 * 
	 * @param parameters A map of all search fields. Should not contain special parameters such as 'limit' or 'enforcesql'.
	 * @param limit
	 *            SQL query limit. May be null, but will then be set to 1000 as default. Can never be higher than 10000.
	 * @param page
	 *            SQL query offset, skips the given number of results. May be null.
	 * @param retrieveRecords
	 *            Set to true to not only retrieve Handle names, but also full records content.
	 * @return A list of Handles.
	 * @throws SQLException
	 */
	public Object genericSqlSearch(MultivaluedMap<String, String> parameters, Integer limit, Integer page, boolean retrieveRecords) throws SQLException {
		if (parameters.isEmpty()) {
			return new LinkedList<String>();
		}
		ReverseLookupConfig config = ReverseLookupConfig.getInstance();
		DataSource dataSource = config.getHandleDataSource();
		Connection connection = null;
		PreparedStatement statement = null;
		ResultSet resultSet = null;
		try {
			connection = dataSource.getConnection();
			StringBuffer sb = new StringBuffer();
			List<String> stringParams = new LinkedList<String>();
			if (parameters.size() == 1) {
				// Simple query, no joins
				String key = parameters.keySet().iterator().next();
				makeSearchSubquery(key, parameters.get(key), sb, stringParams, limit, page, retrieveRecords);
			} else {
				// Search for Handles with several type entries to be checked
				// using multiple inner joins
				sb.append("select table_1.handle from ");
				int tableIndex = 1;
				for (String key : parameters.keySet()) {
					if (tableIndex > 1)
						sb.append(" inner join ");
					sb.append("(");
					makeSearchSubquery(key, parameters.get(key), sb, stringParams, null, null, false);
					sb.append(") table_" + tableIndex);
					if (tableIndex > 1)
						sb.append(" on table_" + (tableIndex - 1) + ".handle=table_" + tableIndex + ".handle");
					tableIndex++;
				}
				if (limit != null)
					sb.append(" limit " + Math.min(limit, 10000));
				else sb.append(" limit 1000");
				if (page != null)
					sb.append(" offset " + page);
			}
			// Now fill statement with stringParams
			statement = connection.prepareStatement(sb.toString());
			Iterator<String> paramsIter = stringParams.iterator();
			int index = 1;
			while (paramsIter.hasNext()) {
				statement.setString(index, paramsIter.next());
				index++;
			}
			// Execute statement
			resultSet = statement.executeQuery();
			if (retrieveRecords) {
				// Result will be a list of map, because we have to store multiple values
				HashMap<String, LinkedList<HashMap<String, String>>> results = new HashMap<String, LinkedList<HashMap<String, String>>>();
				while (resultSet.next()) {
					HashMap<String, String> pair = new HashMap<>();
					pair.put("type", resultSet.getString(2));
					pair.put("value", resultSet.getString(3));
					LinkedList<HashMap<String, String>> handlevalues = results.get(resultSet.getString(1));
					if (handlevalues == null) {
						LinkedList<HashMap<String, String>> list = new LinkedList<>();
						list.add(pair);
						results.put(resultSet.getString(1), list);
					}
					else {
						handlevalues.add(pair);
					}
				}
				return results;
			}
			else {
				// Result will be a simple list of Handle names
				List<String> results = new LinkedList<String>();
				while (resultSet.next()) {
					results.add(resultSet.getString(1));
				}
				return results;
			}
		} finally {
			if (resultSet != null) {
				try {
					resultSet.close();
				} catch (SQLException e) {
					// swallow
				}
			}
			if (statement != null) {
				try {
					statement.close();
				} catch (SQLException e) {
					// swallow
				}
			}
			if (connection != null) {
				try {
					connection.close();
				} catch (SQLException e) {
					// swallow
				}
			}
		}
	}

	private void makeSearchSubquery(String key, List<String> list, StringBuffer sb, List<String> stringParams, Integer limit, Integer page, boolean retrieveRecords) {
		if (retrieveRecords) {
			sb.append("select handle, type, data from handles as allvalues inner join (select handle as subhandle from handles where type=?");
		}
		else {
			sb.append("select handle from handles where type=?");
		}
		stringParams.add(key);
		for (String value : list) {
			String modvalue = value;
			if (modvalue.contains("*")) {
				modvalue = modvalue.replace("*", "%");
				sb.append(" and data like ?");
			} else {
				sb.append(" and data=?");
			}
			stringParams.add(modvalue);
		}
		if (limit != null)
			sb.append(" limit " + limit);
		if (page != null)
			sb.append(" offset " + page);
		if (retrieveRecords)
			sb.append(") subtable on allvalues.handle=subtable.subhandle"); // close sub-select; limit/page be applied to it rather than the outer select
	}

}
