# B2HANDLE-HandleReverseLookupServlet

B2HANDLE-HRLS provides a Java servlet that will enable reverse-lookup and searching against a local Handle server installation with SQL storage.

## How to build

This is a Maven-enabled project. To build a .war file, install [Apache Maven](https://maven.apache.org) and then call:
```
$ mvn clean
$ mvn compile
$ mvn war:war
```
The .war file will be under subdirectory "target". 

## How to build on Linux 8 (RedHat 8 flavour systems)

This is a Maven-enabled project. To build a .war file, install [Apache Maven](https://maven.apache.org) and then call:
```
$ mvn clean   -Denv=linux8
$ mvn compile -Denv=linux8
$ mvn war:war -Denv=linux8
```
The .war file will be under subdirectory "target". 

This was tested with the following versions and settings:
```
$ mvn --version
Picked up JAVA_TOOL_OPTIONS: -Dfile.encoding=UTF8
Apache Maven 3.5.4 (Red Hat 3.5.4-5)
Maven home: /usr/share/maven
Java version: 17.0.5, vendor: Red Hat, Inc., runtime: /usr/lib/jvm/java-17-openjdk-17.0.5.0.8-2.el8_6.x86_64
Default locale: en_US, platform encoding: UTF8
OS name: "linux", version: "4.18.0-425.3.1.el8.x86_64", arch: "amd64", family: "unix"
```

## How to deploy (using embedded Handle System v8 (or higher) Jetty)

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
sqlConnectionString = jdbc\:\mysql\://localhost\:3306/database_name?autoReconnect=true&serverTimezone=Europe/Amsterdam
sqlUsername = user
sqlPassword = password
jdbcDriverClassName = com.mysql.jdbc.Driver
```

Note the escaping of colon characters in the the sqlConnectionString.
Note the setting of the timezone. If this is not set the servlet will not start and complain about
```
com.mysql.cj.exceptions.InvalidConnectionAttributeException
```

By default, the servlet does not log all queries. This can be enabled by including the following in the config file. The query log will be under the location {HANDLE_SVR}/logs/hrls-requests.log. 

```
logAllQueries = true
``` 

These logs will be rotated daily and no more than 28 logs will be kept. These parameters can be overridden by customizing the log4j2.xml file contained in the war. You can specify a location for your own log4j2.xml file using a java parameter: -Dlog4j.configurationFile=path/to/log4j2.xml

You can also specify optionally a custom service name for the servlet. This will be used for logging purposes but does not affect interaction with the databases.

```
serviceName = MyService
```

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

And some curl examples are:

curl -u "username:password" https://your.server:port/hrls/ping

curl -u "username:password" https://your.server:port/hrls/handles?URL=*

curl -u "username:password" https://your.server:port/hrls/handles/11112?URL=*

curl -u "username:password" https://your.server:port/hrls/handles?URL=http://www.test.com&EMAIL=mail@test.com

curl -u "username:password" https://your.server:port/hrls/handles?URL=*&limit=20

curl -u "username:password" https://your.server:port/hrls/handles?URL=*&limit=20&page=0

To retrieve full Handle records, set the optional "retrieverecords" parameter to true:

https://your.server:port/hrls/handles?URL=*&retrieverecords=true

**NOTE:** Retrieving records will not decode HS_ADMIN record fields.

**NOTE:** `retrieverecords=true` with a limit of 100000 might give a server error: _HTTP ERROR 500_. The handle logfile shows _java.lang.OutOfMemoryError: GC overhead limit exceeded_. To prevent this increase the memory for the handle server during startup. An example is _-Xmx2G_.

**NOTE:** The maximum of limit is 100000. The default of limit is 1000. By default it will only show 1000 matches when searching.


## License

Copyright 2015-2019, Deutsches Klimarechenzentrum GmbH, SURFsara, Gesellschaft für Wissenschaftliche Datenverarbeitung Göttingen mbH.

The HRLS software is licensed under the Apache License, Version 2.0 (the "License"); you may not use this product except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
