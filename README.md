# B2HANDLE-HandleReverseLookupServlet

B2HANDLE-HRLS provides a Java servlet that will enable reverse-lookup and searching against local a Handle server installation with SQL storage.

## How to build

This is a Maven-enabled project. To build a .war file, install [Apache Maven](https://maven.apache.org) and then call:
```
$ mvn compile
$ mvn war:war
```
The .war file will be under subdirectory "target". 

## How to deploy (using embedded Handle System v8 Jetty)

To deploy the servlet .war in the embedded jetty, copy it to your-instance-directory/webapps.
The servlet also needs configuration. Most importantly, the servlet requires an environmental variable **HANDLE_SVR** which should point to the Handle server instance's home directory from which the servlet will load its configuration file.

Please make sure you are using a JDBC4 database connector; if you are using a JDBC3 connector, you will have to reconfigure c3p0 (see below).

### Step by step guide for deployment

The path {HANDLE_HOME} is the home directory of the target Handle server, for example ~/hs/svr_1.

1. Copy the .war to {HANDLE_HOME}/webapps.
2. Accessing the servlet's web methods requires authentication. Currently, HTTP Basic Authentication is supported. To enable this, a file {HANDLE_HOME}/realm.properties must be created. The format of this file is described further below. The rolename for Handle search is "handle-search".
3. The servlet requires a properties file {HANDLE_HOME}/handlereverselookupservlet.properties with details on how to connect to the SQL or Solr storage for searching. The full format of this file is given further below. (If deployed via Tomcat, the parameters should be provided as Servlet init params via context.xml.)
4. If you configure the servlet for SQL access, you need to place the driver's .jar file in the Handle Server's lib directory.
5. Start your Handle server.
6. The reverse lookup service can be accessed under the server's subpath /hrls. A simple test may be to call http://your.server/hrls/ping - this should ask for authentication.

### Servlet properties configuration file format

The handlereverselookupservlet.properties file format is as follows. The file consists of two blocks, one for SQL and one for Solr. At least one of either must be present.

```
useSql = true
sqlConnectionString = (your SQL connection string)
sqlUsername = (user)
sqlPassword = (password)
jdbcDriverClassName = (your JDBC driver class name)

useSolr = true
solrCollection = (name of your Solr collection)
solrCloudZkHost = (Zookeeper host and port)
```

A typical configuration for EUDAT for Handle servers that use SQL storage may be:

```
useSql = true
useSolr = false
sqlConnectionString = jdbc\:\mysql\://localhost\:3306/database_name?autoReconnect=true
sqlUsername = user
sqlPassword = password
```

Note the escaping of colon characters in the the sqlConnectionString. 

### Security realm configuration file format

The full description is available here, under HashLoginService: http://wiki.eclipse.org/Jetty/Tutorial/Realms

Example:
```
username: password, handle-search
```

## Further database connection customization

The servlet uses [c3p0](http://www.mchange.com/projects/c3p0) for SQL connection pooling. C3P0 has quite elaborate configuration options; HRLS sets some default options through its own c3p0.properties file. Please refer to the c3p0 documentation to learn how to override them if required.

## Example test calls

After everything is set up, you can test the basic functionality using a browser.
Call the following URL:

https://your.server/hrls/ping

This should ask for authentication (credentials from the realm.properties file) and return "OK".
To check whether the actual reverse lookup works, create some Handles on the server and then retrieve all of them with the following call:

https://your.server/hrls/handles?URL=*

And a curl example would be:

curl -u "<username>:<password>" https://your.server:port/hrls/ping

curl -u "<username>:<password>" https://your.server:port/hrls/handles?URL=*
