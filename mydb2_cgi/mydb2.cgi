 #!/user/bin/perl 
 use strict;
 use warnings;
 use CGI;
 use DBI;
 use DBD::ODBC;
 use Data::Dumper;
 
 use vars qw($DBH %CONFIG $PRINT_HEADER $VERSION %DB2_TYPES);
  $DBH = undef; 
  $PRINT_HEADER = 0; 
  $VERSION = '1.09';
  %CONFIG = ( script_url      => 'mydb2.cgi',
			  page_length     => 40,
			  default_sort    => 0,
			  insert_null     => 1,
			  home_url        => 'mydb2.cgi',
			  insert_origin   => 'insert',
			  schema          => '',
			  debug           => undef,
			  autologin       => 1,
			  show_timestamp_field => 1,
			  data_source     => 'dbi:ODBC:',
			  table_count     => 20,
			  tables_page     => 50,
			  
			  );
  #ODBC driver doesn't return the correct type name
  # Will create a hash table as a crosswalk
 %DB2_TYPES = ( 4 => 'INTEGER',
				-8 => 'VARCHAR',
				93 => 'TIMESTAMP',
				91 => 'DATE',
				5  => 'SMALLINT',
				8  => 'DOUBLE',
				3  => 'DECIMAL',
			   -9  => 'VARGRAPHIC',
			   -10 => 'LONG VARGRAPHIC',
				7  => 'REAL',
				92 => 'TIME',
			   -98 => 'BLOB',
			   -99 => 'CLOB',		
			  -350 => 'DBCLOB',
			    -5 => 'BIGINT',
			  -360 => 'DECFLOAT',
 );
 eval{&init_flow;};
 
 

# Directs traffic to correct sub based on do=level
 sub init_flow{
 my $in = new CGI;
 my $level;
 #print "inside init_flow()\n";
    if (defined ($in->param('db_user')) || defined ($in->param('db_host'))) { &do_login($in); }
    else { 
        $level = $in->param("do") || '';
      #print Dump($in);
        if ($level eq "logout") { 
            &do_logout($in); 
            if ( $CONFIG{'debug'} ) {&cgierr("debug");}
            return 1; 
        }
        
        #if (($level ne "login") && !$in->param('form_login') ){ &assign_cookies($in); } 
        #else { if (!$PRINT_HEADER) { print $in->header(); $PRINT_HEADER=1} }

        if ($CONFIG{'direct_connect'} && !$in->param) {$level = 'tables';}
        
        if (!$level)                      { show_dbs($in); }           # Diplay the database list.
        elsif ($level eq "database")      { modify_db($in); }          # Create or drop a database.
        elsif ($level eq "login")         { html_login($in); }         # Prompt the log-in page when needed.
        elsif ($level eq "tables")        { &show_tables($in); }        # Display the list of tables.
		elsif ($level eq "views")        { &show_views($in);}           # Display the list of views
        elsif ($level eq "browse")        { &table_browse($in); }       # Do a general browse.
        elsif ($level eq "select")        { &table_select($in); }       # Compose query criteria for browse.
        elsif ($level eq "insert")        { &html_insert($in); }        # Input value for insert.
        elsif ($level eq "insert_record") { &insert_record($in); }      # Insert the value input into table.
        elsif ($level eq "property")      { &table_property($in); }     # Display column spec's of the current table.
        elsif ($level eq "modify")        { &table_modify($in); }       # Modify the table contents.
        elsif ($level eq "create")        { &html_table_def($in,'create'); }    # Construct the specifications of the new table.
        elsif ($level eq "create_table")  { &create_table($in); }       # Create a new table according to the specification.
        elsif ($level eq "alter_table")   { &alter_table($in); }        # Change the structure of a table.
        elsif ($level eq "add_col")       { &html_table_def($in,'add_col'); }   # Add new column(s) to a table.
        elsif ($level eq "sql_monitor")   { sql_monitor($in); }        # Process query entered in SQL Monitor.
        elsif ($level eq "sql_monitor_file") { sql_monitor_file($in); }# Process queries saved in a file. 
        elsif ($level eq "import")        { import_record($in); }      # Do import from file.
        elsif ($level eq "export")        { &export_record($in); }      # Do export to file.
        elsif ($level eq "mysqldump")     { mysqldump($in); }          # Create a table dump into file specified.
        elsif ($level eq "top_level_op")  { &top_level_op($in); }       # Create db/create table/SQL Monitor/import/export/
                                                                        # add fields/rename table.
		elsif ($level eq "show_query")	  { html_show_query($in); }	# display saved query in SQL monitor.
		elsif ($level eq "save_search")	  { &html_save_search($in); }
        elsif ($level eq "help")          { html_help($in); }          # display help pages
        else { cgierr("fatal error: $@"); }                            # Display error message if error occurs.
        
        if ($DBH) {$DBH->disconnect();}
    }
    if ( $CONFIG{'debug'} ) {&cgierr("debug");}
    return 1;
}
#=================================================#
#             Top Level Operations                #
#=================================================#

sub top_level_op{
# ---------------------------------------------------
# Determine which top level operation page to display.

    my $in = shift;
    my $action = $in->param('action') || '';
    if      ($action eq 'create_db')    {&html_create_db($in)}
    elsif   ($action eq 'sql_monitor')  {&html_sql_monitor($in)}
    elsif   ($action eq 'create_table') {&html_create_table($in)}
    elsif   ($action eq 'import')       {&html_import($in, &table_field_prep($in))}
    elsif   ($action eq 'export')       {&html_export($in, &table_field_prep($in))} 
    elsif   ($action eq 'add_fields')   {&html_add_fields($in)} 
    elsif   ($action eq 'rename_table') {&html_rename_table($in)} 
    elsif   ($action eq 'mysqldump')    {&html_mysqldump($in)} 
    else {&cgierr("Action cannot be identified in top level operation.")}
}
sub print_html_start{
  return "<!DOCTYPE html>\n<html>\n<body>";
 
}
sub html_create_field{
  my $field_num = shift;
     #$field_num++;
  my $text;
  $text = qq{
         <tr>
<td width="103" height="1">
   <INPUT TYPE="text" NAME="field_};
  $text .= $field_num;
  $text .= qq{">
				</td>
				<td width="103" height="1" valign="middle" align="center">
				   <select size="1" name="type_};
   $text .= $field_num;
   $text .= qq{">
					<option>BIGINT</option>
					<option>CHAR</option>
					<option>DATE</option>
					<option>DECIMAL</option>
					<option>DOUBLE</option>
					<option>INTEGER</option>
					<option>REAL</option>
					<option>DECFLOAT</option>
					<option>SMALLINT</option>
					<option>TIMESTAMP</option>
					<option>BLOB</option>
					<option>DBCLOB</option>
					<option>CLOB</option>
					<option>XML</option>
					<option>VARCHAR</option>
					<option>LONG VARCHAR</option>
					<option>GRAPHIC</option>
					<option>VARGRAPHIC</option>
					<option>LONG VARGRAPHIC</option>
				   </select>
				</td>
				<td width="103" height="1">
				   <INPUT TYPE="text" NAME="length_set_};
   $text .= $field_num;
   $text .= qq{">
				</td>
				<td width="103" height="1">
				   <select size="1" name="attributes_};
	$text .= $field_num;
	$text .= qq{">
					<option></option>
					<option>BINARY</option>
					<option>UNSIGNED</option>
					<option>UNSIGNED ZEROFILL</option>
				   </select>
				</td>
				<td width="103" height="1">
				   <select size="1" name="null_};
	$text .= $field_num;
	$text .= qq{">
					<option>NULL</option>
					<option>NOT NULL</option>
				   </select> 
				</td>
				<td width="103" height="1">
				   <INPUT TYPE="text" NAME="default_};
	$text .= $field_num;
	$text .=  qq{">
				</td>
				<td width="103" height="1" valign="middle" align="center">
				   <select size="1" name="extra_};
	$text .= $field_num;
	$text .=  qq{">
					<option></option>
					<option>INCREMENT</option>
				   </select>
				</td>
				<td width="54" height="1" align="center" valign="middle">
				   <input type="checkbox" name="primary_};
	$text .= $field_num;
	$text .=  qq{" value="ON"></p>
				</td>
				<td width="45" height="1" valign="middle" align="center">
				   <input type="checkbox" name="index_};
	$text .= $field_num;
	$text .=  qq{" value="ON"></p>
				</td>
				<td width="51" height="1" valign="middle" align="center">
				   <input type="checkbox" name="unique_};
	$text .= $field_num;
	$text .=  qq{" value="ON"></p>
				</td>
				</tr>};

 return $text;

}
sub table_property{
# ---------------------------------------------------
# The function outputs the result of "describe table_name"
# query.  It reads the output row by row and create 
# Change/Drop/Primary/Index/Unique links with each field.

    my ($in, $feedback) = @_;
	#print Dump($in);
    my ($page, $query, $sth, @ary, $table_property, $table_property_row);

    my $data_source = $CONFIG{'data_source'} || '';
    my $table       = $in->param("table")       || '';


    $DBH = &connect_db($in) or return; 
    #$query = "describe $table";
	$query = "SELECT COLNAME,TYPENAME,LENGTH,SCALE,NULLS from syscat.columns where tabname='".$table."'";
	#print "query= ".$query."\n";
    $sth = &exec_query($query) or return;
	#print $sth."\n";
    #print Dump($sth);
    # Display the contents in the table selected.
    while ( @ary = $sth->fetchrow_array() ) {
        $table_property_row .= "\n<TR><TD>" . join ( "</TD><TD>" , @ary) . "</TD>";
        $table_property_row .= qq~\n\t<TD><A href="$CONFIG{'script_url'}?do=alter_table&table=$table&col=$ary[0]&action=alter_col">Change</A></TD>~;
        $table_property_row .= qq~\n\t<TD><A href="$CONFIG{'script_url'}?do=alter_table&table=$table&col=$ary[0]&action=drop_col">Drop</A></TD>~;
        $table_property_row .= qq~\n\t<TD><A href="$CONFIG{'script_url'}?do=alter_table&table=$table&col=$ary[0]&action=set_primary">Primary</A></TD>~;
        $table_property_row .= qq~\n\t<TD><A href="$CONFIG{'script_url'}?do=alter_table&table=$table&col=$ary[0]&action=set_index">Index</A></TD>~;
        $table_property_row .= qq~\n\t<TD><A href="$CONFIG{'script_url'}?do=alter_table&table=$table&col=$ary[0]&action=set_unique">Unique</A></TD></TR>~;
		#print $table_property_row."\n";
    }
    $sth->finish();

    # for display purpose, each empty cell is replace with a space.
    $table_property_row =~ s/<TD><\/TD>/<TD>\&nbsp\;<\/TD>/g;
    #print Dump($table_property_row);
    #$query = "describe $table";
	#$query = "SELECT COLNAME,TYPENAME,LENGTH,SCALE,NULLS from syscat.columns where tabname='".$table."'";
    $sth = &exec_query($query) or return;
    #print "sth NAME =".$sth->{NAME}."\n";
    # Construct the table.
    $table_property  = "<TABLE BORDER=2>";
    $table_property .= "<TR><TD><B>". join ("</TD><TD><B>", @{$sth->{NAME}}) . "</TD><TH colspan=5>ACTION</TH></TR>\n";
    $table_property .= $table_property_row;
    $table_property .= "</TABLE>";
	#print $table_property."\n";
    $sth->finish();
    
    &html_property($in, $table_property, $feedback);
}

# ====================== #
#    Create New Table    #
# ====================== #

sub create_table{
# ---------------------------------------------------
# This function takes in the input from the create table 
# form and put them together to produce a create table 
# query.

    my $in = shift;
    my $table = $in->param('table') || '';
    my (@field_list, $col_spec, @primary_list, @index_list, @unique_list, $fields, $primary, $index, $unique, $sth, $query);


    $DBH = &connect_db($in) or return; 

    # get the specification of each column.
    for (my $i = 0; $i < $in->param('num_of_fields'); $i++) {

        # Make the text input fields into a string to fit in the query.
        $col_spec = &concate_col_spec($in, $i);
         print $col_spec;
        push (@field_list, "$col_spec");
        
        # Check index fields.
        if ( $in->param("primary_$i") ) { push (@primary_list, $in->param("field_$i")); }
        if ( $in->param("index_$i") )   { push (@index_list, $in->param("field_$i")); }
        if ( $in->param("unique_$i") )  { push (@unique_list, $in->param("field_$i")); }
    }
    
    $fields  = join ",", @field_list;
    $primary = join ",", @primary_list;
    $index   = join ",", @index_list;  
    $unique  = join ",", @unique_list;
    if(defined($CONFIG{'schema'})){
	 $query = 'CREATE TABLE '.$CONFIG{'schema'}.'.'."$table($fields";
	}else{
    $query = "CREATE TABLE $table($fields";
	}
    if ($primary){ $query .= ", PRIMARY KEY ($primary)" }
    if ($index)  { $query .= ", INDEX ($index)" }
    if ($unique) { $query .= ", UNIQUE ($unique)" }

    $query .= ')';
    
    $sth = &exec_query($query) or return;
    $sth->finish();
    
    &show_tables($in, "Table $table Created.");
}
sub concate_col_spec{
# ---------------------------------------------------
# Reconstruct the input variables into a string in the form 
# "field_name(type(length_set) attribute DEFAULT default_value extra)"
# Example of output for auto increment in DB2
#CREATE TABLE "UMWR484".mytable2 (
#  ID	INTEGER	NOT NULL	GENERATED BY DEFAULT
#    AS IDENTITY (START WITH 1, INCREMENT BY 1, CACHE 20,
#       NO MINVALUE, MAXVALUE 0, NO CYCLE, NO ORDER),
#  desc	VARCHAR(20)
#);
    my ($in, $i) = @_;
    my $col_spec;
    
    $col_spec = '';
    $col_spec .= $in->param("field_$i") . ' ';
    $col_spec .= $in->param("type_$i");
    if ( $in->param("length_set_$i") ) { $col_spec .= '(' . $in->param("length_set_$i") . ')'; }
    $col_spec .= ' ' . $in->param("attributes_$i") . ' ';
    $col_spec .= $in->param("null_$i") . ' ';
    if ( $in->param("default_$i") ) { $col_spec .= qq{GENERATED ALWAYS AS };
									  $col_spec .= $in->param("default_$i");
									  }
	if($in->param("extra_$i") eq "INCREMENT"){
	$col_spec .= qq{(START WITH 1, INCREMENT BY 1, NO CACHE)};
		}
    #$col_spec .= $in->param("extra_$i");
    #print $col_spec;
    return $col_spec;
}

sub html_property{
# --------------------------------------------------------
# Displays the specificaions of a table. 
#     $table_property: the table that consists of the table spec's
#                      and action links (change/drop/primary/index/unique).
#     key_table      : the table that shows the keys in the table.
#     $feedback      : feedback message of any action performed before 
#                      arriving the page.
     
    
    my ($in, $table_property, $feedback) = @_;
    my ($text,$do,$home_url,$script_url,$data_source,$db,$table,$key_table,
	   $help_topic,$version); 
	
	$do              = $in->param('do');
	$home_url        = $CONFIG{'home_url'};
	$script_url      = $CONFIG{'script_url'}; 
	$data_source     = $CONFIG{'data_source'};
	$db              = &get_db($CONFIG{'data_source'}) ||'';
	$table           = $in->param('table');
	$key_table       = &get_key_table($in);
	$feedback        = &html_escape($feedback);
	$help_topic      = "properties";
	$version         = $VERSION;
      # print "Inside html_property\n";                             
	$text = qq{<HTML>
				<HEAD><TITLE>
				MyDB2Man: Table Property
				</TITLE></HEAD>
				<BODY BGCOLOR="#CCCCCC">
				<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
							<tr><td bgcolor="navy">
									<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
									<b>MyDB2Man: Table Property</b>
							</td></tr>
							<tr><td>};
	#print $text;						
	$text .= &html_header($in);
	$text .= qq{<UL>};
			if ($feedback){
				$text .= &message_html($feedback);
				$text .= "<P>";
				}
	$text .= qq{$table_property
				<P>
				<UL>};
			if($key_table){
				$text .= qq{<B><li> Keys:</B>
							$key_table};
				}
	$text .=	qq{</UL>
				</UL>
				</td></tr></table>
				</BODY></HTML>};
	print $text;
}
sub table_modify{
# ---------------------------------------------------
# Determine modify action.

    my $in = shift;
    my $action = $in->param('action') || '';

    if      ($action eq 'drop_table')   { &drop_table($in); }
    elsif   ($action eq 'empty_table')  { &empty_table($in); }
    elsif   ($action eq 'delete_record'){ &delete_record($in); }
    elsif   ($action eq 'edit_record')  { &edit_record_html($in); }
    elsif   ($action eq 'update')       { &update_record($in) }
    else    { &cgierr("modify action cannot be identified"); }
}

sub edit_record_html{
# ---------------------------------------------------
# Pre-processing stage before the edit record form is 
# displayed.  This function prepares necessary information
# for the edit form.
# $record_modify consists the primary key(s)
# value of the record being edited.
# i.e. key = value.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $record_modify = $in->param('record_modify') || '';
    my ($sth, $query, @record, $update, $update_fields);

    
    $DBH = &connect_db($in) or die print $DBH->err,"<br>"; #return; 
    
    # Get the record being modified.
    $query = "SELECT * FROM ";
	if(defined($CONFIG{'schema'})){
	$query .= $CONFIG{'schema'}.'.';
	}
	$query .= "$table WHERE $record_modify FOR FETCH ONLY";  
	#print $query,"<br>"; 
	#print "edit_record_query = ".$query."<br>";
    $sth = &exec_query($query);#or return;
	#@record = $DBH->selectrow_array($query);
    @record = $sth->fetchrow_array();
    $sth->finish();
    
    # create the the edit record form table.
	#print Dumper(@record);
    $update_fields = &form_fields($in, 1, @record);
    &html_update($in, $update_fields);
}
sub update_record{
# ---------------------------------------------------
# Take in the input from the edit table form and update 
# the record specified.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $record_modify = $in->param('record_modify') || '';
    my ($sth, $query, $update, @fields);


    $DBH = &connect_db($in) or return; 
    
    # Get the updated values in each field.  Each element in the 
    # field is in the form "field = value".
    @fields = &compose_new_condition($in);

    $update = join ",", @fields;
    $query = "UPDATE $table SET $update WHERE $record_modify";  
    $sth = &exec_query($query) or return;
    $sth->finish();
    
    &table_browse($in);
}

sub html_table_def{
# --------------------------------------------------------
# lets the user construct the specificaitons of fields/columns. 
# Used when creating a new table or adding new field(s)/column(s).
# If a new table is to be created, the table name is first checked to 
# see if it is a valid one.  Then the number of fields/columns is checked
# also for its validity.
#     $columns: the input table that lets user to construct field/column
#               spec's.        
#

    my ($in, $action) = @_;
    my ($columns,$do);

    if ($action eq 'create') { $do = 'create_table'; }
    else { $do = 'alter_table'; }
    
    &valid_name_check($in->param('table')) or return;

    if ($in->param('num_of_fields') < 1)    { &sqlerr("Number of fields cannot be less than 0.") }
    elsif ($in->param('num_of_fields')>500) {&sqlerr("Number of fields too large.") }    
    else {
        for (my $i = 0; $i < $in->param('num_of_fields'); $i++) {
		  
            $columns .= &html_create_field($i);    
        }

        &html_create_table_next($in,$do,$columns); 
                                   
    }
}

sub html_export{
# --------------------------------------------------------
# Data export page.

    my ($in, $options, $size) = @_;
	my ($empty,$do,$home_url,$script_url,$data_source,$db,$table,$field_options,$empty_options,$help_topic,$version,$text);
    my $empty_op = '';
    
    for (my $i; $i<$size; $i++) {
        $empty .= '<OPTION value=""></OPTION>' . "\n";
    }
    
    $size = $size + 1;
    if ($size > 10) {$size = 10;}
    $do= scalar $in->param('do');
    $home_url   = $CONFIG{'home_url'};
    $script_url = $CONFIG{'script_url'};
    $data_source = $CONFIG{'data_source'};
    $db              = &get_db($CONFIG{'data_source'});
    $table           = scalar $in->param('table');
    $field_options   = $options;
    $empty_options   = $empty;
    $size            = $size;
    $help_topic      = 'import';
    $version         = $VERSION;
    $text .= qq{
	
				   <HTML>
			<HEAD>
			<TITLE>MySQLMan: Export to File</TITLE>

			<SCRIPT LANGUAGE="JavaScript">
			<!--

			function AddAll (From, To) {
				var FromObj = document.ExportForm[From];
				var ToObj   = document.ExportForm[To];
				
				var i     = 1;
				var track = 1;
				while (i < FromObj.options.length) {
					if (track == FromObj.options.length) {
						alert ("You can not add more than the number of fields in the select list.");
						return;
					}
					if (ToObj.options[track].value != "") { track++; continue }
					ToObj.options[track].value    = FromObj.options[i].value;
					ToObj.options[track].text     = FromObj.options[i].text;
					ToObj.options[track].selected = true;
					i++;
					track++;
				}
				return true;
			}

			function AddIt (From, To) {
				var FromObj = document.ExportForm[From];
				var ToObj   = document.ExportForm[To];
				
				var track = 1;
				var i     = 1;
				while (i < FromObj.options.length) {
					if (track == FromObj.options.length) {
						alert ("You can not add more than the number of fields in the select list.");
						return false;
					}
					if (ToObj.options[track].value != "") { track++; continue }
					if (FromObj.options[i].selected) {
						ToObj.options[track].value    = FromObj.options[i].value;
						ToObj.options[track].text     = FromObj.options[i].text;
						ToObj.options[track].selected = true;
						track++;
					}
					i++;
				}
				return true;
			}

			function Clear (What) {
				var Obj   = document.ExportForm[What];
				for (var i = 1; i < Obj.options.length; i++) {
					Obj.options[i].value    = "";
					Obj.options[i].text     = "";
					Obj.options[i].selected = false;
				}
				return true;
			} 

			//-->
			</SCRIPT>

			</HEAD>
			<BODY BGCOLOR="#CCCCCC">
			<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
						<tr><td bgcolor="navy">
								<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
								<b>MySQLMan: Export to File</b>
						</td></tr>
						<tr><td>};
		$text .= &html_header($in);
		$text .=  qq{	<UL>

			<table bgcolor="#FFFFCC" border=1 cellpadding=5 cellspacing=3>
			<td>
			<li><B> Export Data from Table <%table%>:</B><BR>
				<UL>
					<FORM METHOD="POST" ACTION="$script_url" name="ExportForm">
					<INPUT TYPE="hidden" NAME=do VALUE='export'>
					<INPUT TYPE="hidden" NAME=table VALUE="$table">
					<INPUT TYPE="hidden" NAME=origin VALUE="property">
					
					<input type="radio" name="export_to_screen" value="1" CHECKED> <B>Export to screen.</B><BR>
					<input type="radio" name="export_to_screen" value="0"> <B>Export to file.&nbsp;&nbsp;
					Path: </B><INPUT TYPE="text" NAME="file" VALUE="" SIZE="45"><P>

					<B>Select fields:</B><BR>
					<INPUT TYPE="radio" NAME="export_all_cols" VALUE="1" checked> All fields<BR>
					<INPUT TYPE="radio" NAME="export_all_cols" VALUE="0"> Selected Fields
					<UL>
						<li>Please note that in the exported file, the order of the data fields will follow the order of<BR>
						fields selected here.
						<P>
						<%include fields_selection.txt%>
						<P>
					</UL>
					
					<B>Options:</B><BR>
					Fields:
					<UL>
					Delimiter: <INPUT TYPE="text" NAME="delimiter" VALUE="|" SIZE="2"><BR>
					Escape Character: <INPUT TYPE="text" NAME="escape_char" VALUE="\" SIZE="2"><BR>
					</UL>
					Records:
					<UL>
					Delimiter: <INPUT TYPE="text" NAME="rec_del" VALUE="\n" SIZE="3"><BR>
					</UL>
					<P>
					<INPUT TYPE="submit" value=" Export ">
					</FORM>
				</UL>
			</td></table>

			</UL>
			</td></tr></table>
			</BODY>
			</HTML>};
	print $text;
}

sub html_import{
 my ($in, $options, $size) = @_;
 my ($empty,$do,$home_url,$script_url,$data_source,$db,$table,$field_options,$empty_options,$help_topic,$version,$text);
 my $empty_op = '';
    
    for (my $i; $i<$size; $i++) {
        $empty .= '<OPTION value=""></OPTION>' . "\n";
    }
    
    $size = $size + 1;
    if ($size > 10) {$size = 10;}
	$do= scalar $in->param('do');
    $home_url   = $CONFIG{'home_url'};
    $script_url = $CONFIG{'script_url'};
    $data_source = $CONFIG{'data_source'};
    $db              = &get_db($CONFIG{'data_source'});
    $table           = scalar $in->param('table');
    $field_options   = $options;
    $empty_options   = $empty;
    $size            = $size;
    $help_topic      = 'import';
    $version         = $VERSION;
	$text  = $in->header();
	$text  .= qq{
	      <HTML>
<HEAD>
<TITLE>MySQLMan: Import From File</TITLE>

<SCRIPT language="Javascript">
<!--
function AddAll (From, To) {
	var FromObj = document.ImportForm[From];
	var ToObj   = document.ImportForm[To];
	
	var i     = 1;
	var track = 1;
	while (i < FromObj.options.length) {
		if (track == FromObj.options.length) {
			alert ("You can not add more than the number of fields in the select list.");
			return;
		}
		if (ToObj.options[track].value != "") { track++; continue }
		for (var l = 1; l < ToObj.options.length; l++) {
			if (ToObj.options[l].value == FromObj.options[i].value) {
				alert ("You can not have duplitcate values for an import.");
				return false;
			}
		}
		ToObj.options[track].value    = FromObj.options[i].value;
		ToObj.options[track].text     = FromObj.options[i].text;
		ToObj.options[track].selected = true;
		i++;
		track++;
	}
	return true;
}

function AddIt (From, To) {
	var FromObj = document.ImportForm[From];
	var ToObj   = document.ImportForm[To];
	var track = 1;
	var i     = 1;
	while (i < FromObj.options.length) {
		if (track == FromObj.options.length) {
			alert ("You can not add more than the number of fields in the select list.");
			return false;
		}
		if (ToObj.options[track].value != "") { track++; continue }
		if (FromObj.options[i].selected) {
			for (var l = 1; l < ToObj.options.length; l++) {
				if (ToObj.options[l].value == FromObj.options[i].value) {
					alert ("You can not have duplitcate values for an import.");
					return false;
				}
			}
			ToObj.options[track].value    = FromObj.options[i].value;
			ToObj.options[track].text     = FromObj.options[i].text;
			ToObj.options[track].selected = true;
			track++;
		}
		i++;
	}
	return true;
}

function Clear (What) {
	var Obj   = document.ImportForm[What];
	for (var i = 1; i < Obj.options.length; i++) {
		Obj.options[i].value    = "";
		Obj.options[i].text     = "";
		Obj.options[i].selected = false;
	}
	return true;
} 

//-->
</SCRIPT>

</HEAD>
<BODY BGCOLOR="#CCCCCC">
<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
			<tr><td bgcolor="navy">
					<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
                    <b>DB2Man: Import From File</b>
			</td></tr>
			<tr><td>};
	$text .= &html_header($in);	
    $text .= qq{
           <UL>
<table bgcolor="#FFFFCC" border=1 cellpadding=5 cellspacing=3>
<tr><td>
<li><B> Import Data to Table $table:</B><BR>
	<UL>
		<FORM ENCTYPE="multipart/form-data" METHOD="POST" ACTION="$script_url" name="ImportForm">
		<INPUT TYPE="hidden" NAME=do VALUE='import'>
		<INPUT TYPE="hidden" NAME=table VALUE="$table">
		<INPUT TYPE="hidden" NAME=origin VALUE="property">

		<table>
	<tr>
	<td><b>File on server.&nbsp;&nbsp;</b></td>
	<td>Path: <INPUT TYPE="text" NAME="server_file" VALUE= "" SIZE="64"></td>
	</tr>
	<tr>
	<td>OR</td>
	</tr>
	<tr>
	<td><b>File on local drive.&nbsp;&nbsp;</b></td>
	<td>Path: <INPUT TYPE="file" NAME="upload_local_file" VALUE= "" SIZE="64"></td>
	</tr>
	</table>
	<P>
		<B>Select fields:</B><BR>
		<INPUT TYPE="radio" NAME="import_all_cols" VALUE="1" checked> All fields<BR>
		<INPUT TYPE="radio" NAME="import_all_cols" VALUE="0"> Selected Fields
		<UL>
			<li>Please note that the order should match the order of the fields in the file.
			<P>
				<table width=80%>
					<tr>
						<td width=45% align="center"><U><B>Fields in table $table</B></U></td>
						<td width=10%></td>
						<td width=45% align="center"><U><B>Fields selected</B></U></td>	
					<tr>
					  <tr>
						<td align="center" valign="center">
						  <select size="$size" name="ImportLeft">
						<option value="">----------------------------</option>
							$field_options
						  </select></td>
						<td align="center" valign="center">
					<!--	 <input type="button" value="Add All &gt;" onclick="AddAll('ImportLeft', 'ImportRight');"><br> -->
						 <input type="button" value="Add &gt;" onclick="AddIt('ImportLeft', 'ImportRight');"><BR><BR>
						 <input type="button" value="Clear" onclick="Clear('ImportRight');"><br>
						</td>
						
						<td align="center" valign="center" rowspan="4">
						  <select size="$size" name="ImportRight" multiple>
						  <option value="">----------------------------</option>
						  $empty_options
						  </select></td>

					  </tr>
					</table>
			</P>
		</UL>

		<INPUT TYPE="checkbox" NAME="local" VALUE="LOCAL" checked> Local Import<BR>
		<INPUT TYPE="checkbox" NAME="replace_op" VALUE="1" checked> Do not show error message if there are duplicate records and do the following:<BR>
		<UL>
		<INPUT TYPE="radio" NAME="replace_act" VALUE="IGNORE" checked>Ignore<BR>
		<INPUT TYPE="radio" NAME="replace_act" VALUE="REPLACE">Replace<BR>
		</UL>
		Fields:
		<UL>
		Delimiter: <INPUT TYPE="text" NAME="delimiter" VALUE="|" SIZE="2"><BR>
		Escape Character: <INPUT TYPE="text" NAME="escape_char" VALUE="\" SIZE="2"><BR>
		</UL>
		Records:
		<UL>
		Delimiter: <INPUT TYPE="text" NAME="rec_del" VALUE="\n" SIZE="3"><BR>
		Ignore first <INPUT TYPE="text" NAME="ignore_line" VALUE="0" SIZE="3"> Lines
		</UL>
		<P>
		<INPUT TYPE="submit" value=" Import ">
		</FORM>
	</UL>
</td></tr></table>

</UL>
</td></tr></table>
</BODY>
</HTML>};	
 print $text;

}
sub html_update{
 my ($in, $insert_fields) = @_;
my ($do,$home_url,$script_url,$data_source,$db,$table,$record_modify,$page,$action,
$sort_index,$fields,$where,$example,$browse_action,$help_topic,$version,$text);
$do              = scalar $in->param('do');
$home_url        = $CONFIG{'home_url'};
$script_url      = $CONFIG{'script_url'}; 
$data_source     = $CONFIG{'data_source'};
$db              = &get_db($CONFIG{'data_source'});
$table           = scalar $in->param('table');
$record_modify   = scalar &html_escape($in->param('record_modify'));
$page            = scalar $in->param('page') || 1;
$action          = scalar $in->param('action');
$sort_index      = scalar &html_escape($in->param('sort_index'));
$fields          = scalar &html_escape($in->param('fields'));
$where           = scalar &html_escape($in->param('where'));
$example         = scalar &html_escape($in->param('example'));
$browse_action   = scalar $in->param('browse_action');
$help_topic      = 'edit';
$version         = $VERSION;
$text  = $in->header();
$text .= qq{
                <HTML>
                <HEAD><TITLE>
                DB2Man: Edit Record
                </TITLE></HEAD>
                <BODY BGCOLOR="#CCCCCC">
                <table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
                            <tr><td bgcolor="navy">
                                    <FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
                                    <b>DB2Man: Edit Record</b>
                            </td></tr>
                            <tr><td>};
                           # print "testing\n";
  $text .= &html_header($in);
            
  $text .=  qq{<UL><FORM METHOD="POST" ACTION="$script_url">
            <INPUT TYPE="hidden" NAME=do VALUE='modify'>
            <INPUT TYPE="hidden" NAME=action VALUE='update'>
            <INPUT TYPE="hidden" NAME=table VALUE="$table">
            <INPUT TYPE="hidden" NAME=browse_action VALUE="$browse_action">
            <INPUT TYPE="hidden" NAME=record_modify VALUE="$record_modify">
            <INPUT TYPE="hidden" NAME=page VALUE="$page">
            <INPUT TYPE="hidden" NAME=sort_index VALUE="$sort_index">
            <INPUT TYPE="hidden" NAME=fields VALUE="$fields">
            <INPUT TYPE="hidden" NAME=where VALUE="$where">
            <INPUT TYPE="hidden" NAME=example VALUE="$example">

            <table>
            <TD bgcolor="#FFFFCC">
            $insert_fields
            <TD>
            </table>
            <P>
            <INPUT TYPE="submit" value=" Go "></FORM>
            </UL>
            </td></tr></table>
            </BODY></HTML>};

 print $text;

}
 
 sub html_create_table{
   my $in = shift;
   my ($do,$home_url,$script_url,$data_source,$db,$table,$help_topic,$version,$text);
   
	$do              = scalar $in->param('do');
	$home_url        = $CONFIG{'home_url'};
	$script_url      = $CONFIG{'script_url'}; 
	$data_source     = $CONFIG{'data_source'};
	$db              = &get_db($CONFIG{'data_source'});
	$table           = scalar $in->param('table');
	$help_topic      = 'create_table';
	$version         = $VERSION;
	
  $text = qq{<HTML>
				<HEAD><TITLE>
				MyDB2: Create New Table
				</TITLE></HEAD>
				<BODY BGCOLOR="#CCCCCC">
				<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
							<tr><td bgcolor="navy">
									<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
									<b>MyDB2: Create New Table</b>
							</td></tr>
							<tr><td>};
				#<%include header.txt%>
  $text .= &html_header($in);
  $text .=				qq{<UL>

				<table bgcolor="#FFFFCC" border=1 cellpadding=5 cellspacing=3>
				<td>
				<FORM METHOD="POST" ACTION="$script_url">
						<INPUT TYPE="hidden" NAME=do VALUE='create'>
						<B>* Create new table on database $db</B><BR>
						<UL>
							Table name: <BR>
							<INPUT TYPE="text" NAME="table" SIZE="20"><BR>
							Number of Fields: <BR>
							<INPUT TYPE="text" NAME="num_of_fields" SIZE="5"><BR>
							<INPUT TYPE="submit" value=" Go ">
						</UL>
					</FORM>
				</td></table>

				</UL>
				</td></tr></table>
				</BODY>
				</HTML>};
		 print $text;		
 }
 
 sub html_create_table_next{
		my($in,$do,$columns) = @_;
        my($home_url,$script_url,$db,$data_source,$table,$num_of_fields,$position,$help_topic,$version);
		
	$home_url        = $CONFIG{'home_url'};
	$script_url      = $CONFIG{'script_url'}; 
	$data_source     = $CONFIG{'data_source'};
	$db              = &get_db($CONFIG{'data_source'});
	$table           = scalar $in->param('table');
	$columns         = $columns;
	$num_of_fields   = scalar $in->param('num_of_fields');
	$position        = scalar $in->param('position');
	$help_topic      = 'col_def';
	$version         = $VERSION;
	
                                    
  my $text;
    $text  = $in->header();
   $text .= qq{HTML>
				<HEAD>
				<TITLE>MyDB2Man: Create New Table</TITLE>
				</HEAD>

				<BODY BGCOLOR="#CCCCCC">
				<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
							<tr><td bgcolor="navy">
									<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
									<b>MyDB2Man: Create New Table</b>
							</td></tr>
							<tr><td>};
	$text .= &html_header($in);

	$text .= qq{<FORM METHOD="POST" ACTION="$script_url">
				<INPUT TYPE="hidden" NAME="do" VALUE="$do">
				<INPUT TYPE="hidden" NAME="table" VALUE="$table">
				<INPUT TYPE="hidden" NAME="num_of_fields" VALUE="$num_of_fields">
				<INPUT TYPE="hidden" NAME="action" VALUE="add_col">
				<INPUT TYPE="hidden" NAME="position" VALUE="$position">


				<table border="2" bgcolor="#FFFFCC">

				  <tr>
					<th>Field</th>
					<th>Type</th>
					<th>Length/Set</th>
					<th>Attributes</th>
					<th>Null</th>
					<th>Default</th>
					<th>Extra</th>
					<th>Primary</th>
					<th>Index</th>
					<th>Unique</th>
				  </tr>

				$columns

				</table><P>};
		if ($do eq 'create_table'){
				$text .= qq{<INPUT TYPE="submit" value=" Create Table ">};
			}
		if ($do eq 'alter_table'){
				
				$text .=qq{<INPUT TYPE="submit" value=" Add Column ">};
		}

		$text .= qq{</FORM>
				</td></tr></table>
				</BODY></HTML>};
	print $text;
 }
sub show_tables {
# ---------------------------------------------------
# Shows all the tables in the database chosen.  Browse/Select
# /Properties/Insert/Drop/Empty links are also created with 
# each table name.

    my $in = shift;
    my ($query, $sth, $table_tables,$data_source);
	#print "inside show_tables()";
	
    $data_source = $CONFIG{'data_source'};
	
	my $name='n/a';
    $DBH = &connect_db or return; 
    #$query = "show tables";
	if(defined($CONFIG{'schema'})){
	 $sth = $DBH->table_info( '', $CONFIG{'schema'}, '', 'TABLE' );
	}else{
    $sth = $DBH->table_info( '', '', '', 'TABLE' );
	}

    $table_tables = '';
	$table_tables .= $in->header();
	$table_tables .= &print_html_start;
	$table_tables .= &html_header($in);
	$table_tables .= qq{<div>};
	# Include Pie Chart that shows table % of space
	 $table_tables .= qq{<iframe width=800px height=500px id="charts" 
							frameborder=0 scrolling=no src="/d3/table-pie-d3.html" seamless></iframe>};
	#$table_tables .= qq{</div>};
	
	$table_tables .= qq{<iframe width=800px height=500px id="charts" 
							frameborder=0 scrolling=no src="/d3/table-bar-d3.html" seamless></iframe></div>};
	$table_tables .= qq{<div>};
	$table_tables .= qq{<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
			<tr><td bgcolor="navy">
					<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
                    <b>Table list</b>
			</td></tr>
			<tr><td></td></tr></table>
			<TABLE border = 2 style="float:left;margin-bottom:10px;margin-left:10px;">
			<TR><TD>#</TD><TD ALIGN="center" width="150px"><B>TABLE</B></TD><TD colspan="3" ALIGN=center>
			<B>ACTION</B></TD></TR>};
	my $rowcount = 0;
    while ( ( undef, undef, $name ) = $sth->fetchrow_array() ) {
		$rowcount++;
        $table_tables .= 
        qq~<TR><TD>$rowcount</TD><TD>$name</TD>
            <TD><A href="$CONFIG{'script_url'}?do=browse&table=$name&page=1&action=browse">Browse</A></TD>
            <TD><A href="$CONFIG{'script_url'}?do=select&table=$name&page=1&action=select">Select</A></TD>
            <TD><A href="$CONFIG{'script_url'}?do=insert&table=$name">Insert</A></TD>
            </TR>\n~;
		if($rowcount % ($CONFIG{'table_count'}) == 0){
		   $table_tables .= qq{</TABLE><TABLE border = 2 style="float:left;margin-bottom:10px;margin-left:10px;">
			<TR><TD>#</TD><TD ALIGN="center" width="150px"><B>TABLE</B></TD><TD colspan="3" ALIGN=center>
			<B>ACTION</B></TD></TR>};
		}
	
    }
	$table_tables .= qq{</TABLE>};
	 if($name eq 'n/a'){
	  $table_tables .= qq{<TABLE border = 2 CELLPADDING= 10>
			<TD><B>There are no Tables in the Database</B></TD>
			</TABLE>};
	 }
	 $table_tables .= qq{</div>};
	 $table_tables .= $in->end_html();
    $sth->finish();
	print $table_tables;
    #&html_table($in, $table_tables, $feedback);
}	

sub show_views {
# ---------------------------------------------------
# Shows all the Views in the database chosen.  Browse/Select
# /Properties/Insert/Drop/Empty links are also created with 
# each View name.

    my $in = shift;
    my ($query, $sth, $table_tables,$data_source);
	#print "inside show_tables()";
	if(defined $in->param("data_source")){
    $data_source = $in->param("data_source");
     }else{
     	$data_source = $CONFIG{'data_source'};
		}
	my $name='n/a';
    $DBH = &connect_db or return; 
	
    $query = "SELECT TABNAME FROM SYSCAT.TABLES WHERE TYPE='V'";
	if(defined($CONFIG{'schema'})){
	 $query .= " AND TABSCHEMA='".$CONFIG{'schema'}."'";
	 }
	 $query .= " ORDER BY TABNAME";
    $sth = &exec_query($query) or return;
    $table_tables = '';
	$table_tables .= $in->header();
	$table_tables .= &print_html_start;
	$table_tables .= &html_header($in);
	$table_tables .= qq{<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
			<tr><td bgcolor="navy">
					<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
                    <b>View list</b>
			</td></tr>
			<tr><td></td></tr></table>
			<TABLE border = 2 style="float:left;margin-bottom:10px;margin-left:10px;">
			<TR><TD>#</TD><TD ALIGN="center" width="150px"><B>VIEW</B></TD><TD colspan="3" ALIGN=center>
			<B>ACTION</B></TD></TR>};
	my $rowcount = 0;
    while ( $name  = $sth->fetchrow_array() ) {
		$rowcount++;
        $table_tables .= 
        qq~<TR><TD>$rowcount</TD><TD>$name</TD>
            <TD><A href="$CONFIG{'script_url'}?do=browse&table=$name&page=1&action=browse">Browse</A></TD>
            <TD><A href="$CONFIG{'script_url'}?do=select&table=$name&page=1&action=select">Select</A></TD>
       
            </TR>\n~;
		if($rowcount % ($CONFIG{'table_count'}) == 0){
		   $table_tables .= qq{</TABLE><TABLE border = 2 style="float:left;margin-bottom:10px;margin-left:10px;">
			<TR><TD>#</TD><TD ALIGN="center" width="150px"><B>VIEW</B></TD><TD colspan="3" ALIGN=center>
			<B>ACTION</B></TD></TR>};
		}
	
    }
	$table_tables .= qq{</TABLE>};
	 if($name eq 'n/a'){
	  $table_tables .= qq{<TABLE border = 2 CELLPADDING= 10>
			<TD><B>There are no VIEWS in the Database</B></TD>
			</TABLE>};
	 }
	 $table_tables .= $in->end_html();
    $sth->finish();
	print $table_tables;
    #&html_table($in, $table_tables, $feedback);
}
sub table_browse{
# ---------------------------------------------------
# Browse, Select/Search
#
#   The function does a "SELECT * FROM table_name" query 
#   to do a browse and will display the results according to 
#   the select criteria specified by user in "select".  If a 
#   primary key exists in the table, then "edit" and "drop" links
#   are also created with each record.
# 
# SQL-Monitor
#
#   A query entered in SQL monitor that requires
#   displaying it's result uses this sub-routine as well.  
#   These queries include explain, select, describe, and desc.

    my ($in) = @_;
    my ($where_clause, $query,$start_row, $empty_set, @pri_key, $prep, $sth, @cols, $rows, @ary, $index,
        $col_name, $table_records, $record, $cells, $page_jump, $page_link, $rows_in_page,
        @fields, @example, @record_modify, $record_modify, $edit_link, @table_list, 
        $table_num, $pri_key_count, $pri_key, $query_printed, $query_count,
		$total_rec_num,$rowcount,@where_col);
    
    my $data_source = $in->param("data_source") || $CONFIG{'data_source'};
    my $table       = $in->param("table")       || $in->param("view") || '';
    my $page        = $in->param("page")        || "1";
    my $action      = $in->param("browse_action") || $in->param("action") || '';
    my $fields      = $in->param("fields")      || '';
    my $where       = $in->param("where")       || '';
    my $example     = $in->param("example")     || '';

    # Some default values
	$record_modify = '';
    if (($page =~ m/\D/))     { 
        &sqlerr("Page number cannot be $page.  Please enter a valid page number."); 
        return;
    }

    # The first row of the page arrived.
    $start_row = (($page - 1) * $CONFIG{'page_length'}); 

    $DBH = &connect_db or return; 

    # get all column names for the table and store them in @cols.
    if ($action eq 'browse' || $action eq 'select') {
        @cols = &get_cols($table);
		
    }
		$fields = join ",",@cols;
		
    if ($action eq 'browse') { 
        #$fields = '*'; 
		
        $index = $in->param("sort_index") || $cols[$CONFIG{'default_sort'}];
    }
    elsif ($action eq 'select') { 

        # SELECT clause.
        if (!$fields) {

            @fields = @cols;
            for (my $i = 0; $i <= $#cols; $i++) {
                if ($in->param("*select_field*_$cols[$i]") ne '') {
                    push( @fields, $in->param("*select_field*_$cols[$i]") );
                }
            }
            #$fields = join ",", @fields;
        }
        
        # WHERE clause.
		
        if ($where) { $where_clause = "WHERE $where"; }

        # Query by example.
        if (!$example) {
            @example = ();
            for (my $i = 0; $i <= $#cols; $i++) {
                if ($in->param("*example*_$cols[$i]") ne '') {
                    my $temp = $cols[$i] . ' like ' . $DBH->quote( $in->param("*example*_$cols[$i]") );
                    push( @example, $temp );
                }
            }
            $example = join " and ", @example;
        }
    
        if ($example) {
            if ($where_clause) { $where_clause .= " and $example"; }
            else { $where_clause = "WHERE $example"; }
        }
        
        # get sort index
        $query = qq~SELECT $fields
                    FROM ~;
		if(defined($CONFIG{'schema'})){
		$query .= $CONFIG{'schema'}.'.';
		}
		$query .= qq~$table 
                    $where_clause
                    FETCH FIRST ROW ONLY~;

        $prep = &exec_query($query) or return;
        $index = $in->param("sort_index") || $prep->{NAME}->[$CONFIG{'default_sort'}];
        $prep->finish();
    }

    @pri_key = ();
    $pri_key = '';

    if ($action eq 'browse' || $action eq 'select') {
        # Prepare the contents in the table selected.
    
        @pri_key = &get_pri_key($table);
        $pri_key = join ",", @pri_key;
		#print "pri_key = ".$pri_key,"\n";
        if ($pri_key ne '') { $pri_key = ',' . $pri_key; }
        
        # the actual query sent to statement handler.  The 
        # primary key is selected for delete and edit.
		# DB2 has no LIMIT command, so will need to hack
		# using ROW_NUMBER() and subquery
		++$start_row;
		$rowcount = $start_row + $CONFIG{'page_length'};
		
		$query = qq{SELECT $fields FROM (SELECT $fields ,row_number() over(ORDER BY $index) as rid FROM };
		if(defined($CONFIG{'schema'})){
		$query .= $CONFIG{'schema'}.'.';
		}
		$query .= qq{$table }; 
						if($where_clause){
		$query .= $where_clause;
		}
		$query .= qq{) as t WHERE t.rid BETWEEN $start_row AND $rowcount};
		#print "query = ".$query."\n";
        #$query = qq~SELECT $fields $pri_key 
         #           FROM $table 
         #           $where_clause   
         #           ORDER BY $index 
         #           LIMIT $start_row, $CONFIG{'page_length'}~;
        
        # The query that gets printed in SQL-Message.
		$query_printed = $query;
        #$query_printed = qq~SELECT $fields
         #                   FROM $table 
         #                  $where_clause   
         #                   ORDER BY $index 
         #                   LIMIT $start_row, $CONFIG{'page_length'}~;

        # counts the total number of resulting records from browse/select
        $query_count =qq~SELECT COUNT(*) 
                         FROM $table ~;
			if($where_clause){			 
           $query_count .= $where_clause;
		   }
        $sth = &exec_query($query_count) or return;
        ($total_rec_num) = $sth->fetchrow();
        $sth->finish();
    }
    else{ # from SQL Monitor.
        if (!$query) { $query = $in->param("query") || ''; }
        @table_list = &get_table_list($query);
        if ($#table_list == 0) { ($table) = @table_list; }
    }
    
    # Get all records or records that satisfy the search criteria.
    # Or, $query is simply the query enter in SQL monitor.
    $sth = &exec_query($query) or return;
    $rows = $sth->rows;
    
    if ($action eq 'monitor') { 
        $total_rec_num = $rows;
        $rows_in_page = $rows - $start_row;
        if ($rows_in_page > $CONFIG{'page_length'}) { $rows_in_page = $CONFIG{'page_length'} }
    }
    else { $rows_in_page = $rows; }

    $page_jump = &link_page_jump($in, $fields, $example, $index, $total_rec_num);

    # Links to next/previous/top page if there is any.
    $page_link = &link_page($in, $rows_in_page, $table, $fields, $example, $index, $total_rec_num);
    
    my $example_esc = $in->escape($example);
    my $where_esc   = $in->escape($where);
    my $query_esc   = $in->escape($query);

    if (!@pri_key) { $pri_key_count = $#pri_key + 1; }
    else {$pri_key_count = 0; }

	#print $#pri_key." \n";
    # Display column names
    $col_name = '';
    if ($action eq 'browse' || $action eq 'select') {
        for (my $i = 0; $i < $sth->{NUM_OF_FIELDS}- $pri_key_count; $i++) {
            $col_name .= qq~\n<TD><B><a href= "$CONFIG{'script_url'}?do=browse&table=$table&page=$page&sort_index=$sth->{NAME}->[$i]&action=$action&fields=$fields&where=$where_esc&example=$example_esc&query=$query_esc">$sth->{NAME}->[$i]</B></TD>~;
			#print $col_name,"\n";
        }
    }
    else {
        for (my $i = 0; $i < $sth->{NUM_OF_FIELDS}- $pri_key_count; $i++) {
            $col_name .= qq~\n<TD><B>$sth->{NAME}->[$i]</B></TD>~;
        }
    }

    $example_esc = &html_escape($example);
	#print "where= ".$where."\n";
    $where_esc   = &html_escape($where);
	#print "where_esc= ".$where_esc."\n";
    $query_esc   = &html_escape($query);

    # Display the contents in the table selected.
    $table_records = '';
    my $counter = 0;

    # Display the resulting set of records.  The result is divided into pages and the page
    # by the length specified in mysql.cfg.
    #
    # From "Browse" or "Select/Search"
    #     The LIMIT clause of the query limits the records to display, so we don't display all.
    # From "SQL Monitor"
    #     Records between $start_row and $start_row+$CONFIG{'page_length'} will be displayed.
    #
    while ( @ary = $sth->fetchrow_array() ) {
        if ($action ne 'monitor' || ($counter >= $start_row && $counter < ($CONFIG{'page_length'} + $start_row))) {
            $record = '';
            @record_modify = ();
				
            for (my $i = 0; $i < $sth->{NUM_OF_FIELDS}; $i++) {
                if ($i < $sth->{NUM_OF_FIELDS} - $pri_key_count) { 
				 # CGI->escape() replaces the commented block of code
					#if (defined($ary[$i])) { 
						#$ary[$i] =~ s/(\r|\n)+/<BR>/g;
						#$ary[$i] =~ s/\t+/&nbsp;&nbsp;&nbsp;/g;
						#$ary[$i] =~ s/\s+/&nbsp;/g;
						#$ary[$i] =~ s/<BR>/<BR>\n/g;
					#}
					
                    if (defined($ary[$i])) { 
                        if ($ary[$i] ne '') { $record .= "<TD>$ary[$i]</TD>"; }

                        # put a space in the cell for display purpose.
                        else { $record .= "<TD>&nbsp;</TD>"; }
                    }
                    else { 
                        if ($CONFIG{'show_null'}) { $record .= "<TD><FONT COLOR=green>NULL</FONT></TD>"; }
                        else { $record .= "<TD><FONT COLOR=green>&nbsp;</FONT></TD>"; }
                    }
                }

                # if there are any primary keys, then push "pri = value"
                # into @record_modify.
                #else{
                    my $cell = $ary[$i];
					my $col_type = $sth->{TYPE}->[$i];
					my $nullable = $sth->{NULLABLE}->[$i];
					
				# for DB2
			    # Need to determine datatype and pass to quote() for proper formating 
                    $cell = $DBH->quote($cell,$col_type);
					#print "cell = ".$cell." length of cell= ".length($cell);
                    my $col_name = $sth->{NAME}->[$i];
					if($nullable ==1 && $cell eq 'NULL'){
					push (@record_modify,  $col_name . ' is NULL ');
					}else{
					push (@record_modify,  $col_name . ' = ' . $cell);
					}
					#print "record_modify = ".@record_modify."\n";
					#print "column type: ".$col_type."\n";
                #}
            }
            if ((! @pri_key) && ($action ne 'monitor')) {
                                
                $record_modify = join ' and ', @record_modify;
				#print "record_modify = ".$record_modify."\n";
                $record_modify = $in->escape($record_modify);

                my ($edit_link, $delete_link);

				$edit_link = qq~<a href= "$CONFIG{'script_url'}?do=modify&table=$table&page=$page&sort_index=$index&fields=$fields&where=$where_esc&example=$example_esc&action=edit_record&record_modify=$record_modify&browse_action=$action">Edit~;
				if ($CONFIG{'confirm_delete_record'}) {
					$delete_link = qq~<a href= "$CONFIG{'script_url'}?do=modify&table=$table&page=$page&sort_index=$index&fields=$fields&where=$where_esc&example=$example_esc&action=delete_record&record_modify=$record_modify&browse_action=$action" onClick="return confirm('Delete the record?')">Delete~;
				}
				else{
					$delete_link = qq~<a href= "$CONFIG{'script_url'}?do=modify&table=$table&page=$page&sort_index=$index&fields=$fields&where=$where_esc&example=$example_esc&action=delete_record&record_modify=$record_modify&browse_action=$action">Delete~;
				}
                $table_records .= 
                qq~<TR>
                $record
                <TD>$edit_link</TD>
                <TD>$delete_link</TD>
                </TR>\n~;
            }
            else { $table_records .= qq~<TR>$record</TR>\n~; }              
        }
        $counter++;
    }
    if (!$record) { $empty_set = 1; }
    else { $empty_set = 0; }

    $sth->finish();

	my $save_search_link = "$CONFIG{'script_url'}?do=save_search&table=$table&page=$page&sort_index=$index&fields=$fields&where=$where_esc&example=$example_esc&action=edit_record&record_modify=$record_modify&browse_action=$action&query=$query_esc";

    &html_table_browse($in, $table, $page_jump, $page_link, $col_name, $table_records, $query, $empty_set, $pri_key, $query_printed, $total_rec_num, $save_search_link);
}

sub table_select {
# ---------------------------------------------------
# This function creates the search form for a SELECT... query (search).
# Field names are in check boxes and "query by example" input 
# fields are created with the check boxes.

    my $in = shift;
    my ($query, $select_fields, $example_fields, $select_table, $example_table, @type_ary, @cols);
    
    my $data_source = $CONFIG{'data_source'} || '';
    my $table       = $in->param("table")       || '';
    my $page        = $in->param("page")        || 1;

    $select_fields  = '';
    $example_fields = '';


    $DBH = &connect_db or return; 

    # Get the names of the all columns.
    @cols = &get_cols($table);

    # fields selection (for SELECT)
    @type_ary = &get_col_type($table); 
    for (my $i = 0; $i <= $#cols; $i++) {
        
        # make the first field checked to avoid error message due to empty select clause.
        if ($i==0) { $select_fields .= qq~\n<input type="checkbox" name="*select_field*_$cols[$i]" value="$cols[$i]" checked>$cols[$i]<BR>~; }
        else       { $select_fields .= qq~\n<input type="checkbox" name="*select_field*_$cols[$i]" value="$cols[$i]">$cols[$i]<BR>~; }
        
        # output the check boxes such that there are 5 rows in a column.
        if ( ($i+1)%5 == 0 ) { $select_fields .= "</TD><TD VALIGN = top>"; }
    
        # compose "query by example" input fields.
        $example_fields .= qq~\n<TR><TD>$cols[$i]</TD><TD>$type_ary[$i]</TD><TD><INPUT TYPE="text" NAME="*example*_$cols[$i]" VALUE="" SIZE="30"></TD></TR>~;
    }   

    $select_table = "<TABLE><TR><TD VALIGN = top>" . $select_fields . "</TD></TR></TABLE>";
    $example_table = "<TABLE BORDER = 1><TR><TH>Fields</TH><TH>Type</TH><TH>Value</TH></TR>" . $example_fields . "</TABLE>";
    
    &html_table_select($in, $select_table, $example_table);
}

sub get_col_type{   
# ---------------------------------------------------
# Gets the type each field/column of the table specified.
# DB2 Column type is found in the 3rd column of query output

    my $table = shift;
    my ($sth, $query, @ary, @type_ary);

    $query = "SELECT COLNAME,TYPENAME,LENGTH,SCALE,NULLS from syscat.columns where tabname='".$table."'";
    $sth = &exec_query($query) or return;
    while (@ary = $sth->fetchrow_array()) {
        push (@type_ary, $ary[1]);
    }
    $sth->finish();
    return @type_ary;
}

sub get_key_table{
# ---------------------------------------------------
# Creates a key/index table.  A "drop" link is created 
# together with each read in.

    my $in = shift;
    my $data_source = $CONFIG{'data_source'} || '';
    my $table = $in->param('table') || '';
    my ($sth, $query, @ary, $unique, $non_unique, $key_name, $column_name, $keys, $key_table);
    
    #$query = "SHOW INDEX from $table";
	$query = "select * from syscat.indexes where tabname='$table'";
	if(defined($CONFIG{'schema'})){
	 $query .= " AND tabschema='$CONFIG{'schema'}'";
	 }
	
    $sth = &exec_query($query) or return;
    while (@ary = $sth->fetchrow_array) {
        my $non_unique  = $ary[8];
        my $key_name    = $ary[1];
        my $column_name = $ary[6];
        if ($non_unique eq 'N') {$unique = 'NO';}
        else {$unique = 'YES';}
        $keys .= qq~<TR><TD>$key_name</TD><TD>$unique</TD><TD>$column_name</TD>
                   <TD><A href="$CONFIG{'script_url'}?do=alter_table&table=$table&action=drop_key&key_name=$key_name">Drop</A></TD></TR>~;
    }
    $sth->finish();
    
    if ($keys) { $key_table = "<TABLE BORDER=2><TR><TH>Key name</TH><TH>Unique</TH><TH>Field</TH><TH>Action</TH></TR>$keys</TABLE>"; }
    else { $key_table = ''; }
    return $key_table;
}
sub get_table_list{
# ---------------------------------------------------
# Gets the list of tables which the query input is querying 
# from.  Since the function is only used in "sub table_browse";
# 

    my $query = shift;
    my (@query, $token, $flag, @table_list, $cur_token, $pre_token, $stop, $cmd, $explain_select, $got_list);

    #strip beginning and ending space.
    $query =~ s/^\s+//;  
    $query =~ s/\s+$//;
    $query =~ s/(\r|\n)+/ /g;

    @query = split /([ ,])/, $query;
    $cmd = lc($query[0]);

    # find table list from:
    # 1. describe / desc
    # 2. explain table 
    if (($cmd eq 'describe') || ($cmd eq 'desc') || ($cmd eq 'explain')) {

        @table_list = ();
        $flag = 0;
        
        for (my $i=1; $i<=$#query;$i++){
            if (defined($query[$i])){
                if (($query[$i] ne '') && ($query[$i] ne ' ') && ($query[$i] ne ',') ){
                    
                    # get the first name after the command.
                    if ($flag == 0) {
                        push (@table_list, $query[$i]);
                        my $tmp = lc($query[$i]);
                        if ($tmp eq 'select') { $explain_select = 1 }
                        $flag = 1;
                    }
                }
            }
        }
        $got_list = 1;
    }

    # find table list from queries like:
    # 1. select queries
    # 2. show queries
    # 3. explain select ....
    if (!$got_list || $explain_select) {
        
        @table_list = ();
        $flag = 0;
        $stop = 0;
        $pre_token = '';

        foreach (@query) {
            if (($_ ne '') && ($_ ne ' ')) {
                $token = lc($_);
                if ($flag == 1) { 

                    # determine the type of the current token.
                    if ($token ne ',') { $cur_token = 'word' }
                    else { $cur_token = 'comma' }

                    # stop then the "from" clause ends
                    if (($cur_token eq 'word') && ($cur_token eq $pre_token) ) { $stop = 1; }
                    
                    if (!$stop && $token ne ',') { push (@table_list, $_) }
                    $pre_token = $cur_token;
                }   
                if ($token eq 'from') { $flag = 1; }
            }
        }
    }
    return @table_list;
}
sub link_page {
# ---------------------------------------------------
# Provides hyperlinks to next, previous, or top pages when needed
    
    my ($in, $rows, $table, $fields, $example, $index, $total_rec_num) = @_;
    my ($data_source, $cur_page, $page, $output, $sort_index, $action, $where, $query, $cur_rec_num, $more_page);
    
    $data_source = $CONFIG{'data_source'} || '';
    $cur_page    = $in->param("page")        || 1;
    $sort_index  = $index;
    $action      = $in->param("browse_action") || $in->param("action") || '';
    $where       = $in->escape($in->param("where")) || '';
    $query       = $in->escape($in->param("query")) || '';
    
    $example = $in->escape($example);

    $cur_rec_num = ($cur_page - 1) * $CONFIG{'page_length'} + $rows;
    if ($cur_rec_num < $total_rec_num) { $more_page = 1; }
    else { $more_page = 0; }


    $output = '';

    # the very first page.
    if ( ($cur_page == 1) and ($rows == $CONFIG{'page_length'}) and ($more_page)) {
        $page = $cur_page + 1; 
        $output .= qq~< <A href="$CONFIG{'script_url'}?do=browse&table=$table&page=$page&sort_index=$sort_index&action=$action&fields=$fields&where=$where&example=$example&query=$query">Next page</A> >~;
    }

    # the very last page.
    elsif ((!$more_page) and ($cur_page != 1)){ 
        $page = $cur_page - 1;
        $output .= qq~< <A href="$CONFIG{'script_url'}?do=browse&table=$table&page=$page&sort_index=$sort_index&action=$action&fields=$fields&where=$where&example=$example&query=$query">Previous page</A> > ~;
    } 

    # any page between the first and the last page.
    elsif ( ($cur_page != 1) and ($rows == $CONFIG{'page_length'}) and ($more_page)){ 
        $page = $cur_page + 1;
        $output .= qq~< <A href="$CONFIG{'script_url'}?do=browse&table=$table&page=$page&sort_index=$sort_index&action=$action&fields=$fields&where=$where&example=$example&query=$query">Next page</A> > ~;
        $page = $cur_page - 1;
        $output .= qq~< <A href="$CONFIG{'script_url'}?do=browse&table=$table&page=$page&sort_index=$sort_index&action=$action&fields=$fields&where=$where&example=$example&query=$query">Previous page</A> > ~;
    }
    # else there is only one page to display.  As a result, no links are available.

    # link to jump back to the first page.
    if (($cur_page != 1)) { 
        $output .= qq~< <A href="$CONFIG{'script_url'}?do=browse&table=$table&page=1&sort_index=$sort_index&action=$action&fields=$fields&where=$where&example=$example&query=$query">Top page</A> >~;
    }
    return $output;
}
sub link_page_jump{
# ---------------------------------------------------
# Produces a text field to let the user enter a number 
# and the user will be brought to the page specified.
    
    my($sth, $table, $where, $action, $query, $data_source, $pages, $output);

    my ($in, $fields, $example, $index, $rows) = @_;

    $data_source = $CONFIG{'data_source'} || '';
    $table       = $in->param("table")       || '';
    $where       = $in->param("where")       || '';
    $action      = $in->param("browse_action") || $in->param("action") || ''; 
    
    $pages = $rows / $CONFIG{'page_length'};
    if (($rows % $CONFIG{'page_length'}) != 0) { $pages = int($pages) + 1 }
    if ($rows > $CONFIG{'page_length'}) {
        return &html_page_jump($in, $pages, $fields, $example, $index); 
    }
    else { return '';}
}

sub html_page_jump{
# --------------------------------------------------------
# displays a text input box that allow user to go to 
# any page of the result table.  
#     pages: total number of pages of the result.

    my ($in, $pages, $fields, $example, $index) = @_;
	my ($action,$table,$where,$query,$data_source);
	$action = $in->param('action');
	 $table = $in->param('table');
	 $where = $in->param('where') || '';
	 $example = &html_escape($example) ;
	 $query = &html_escape($in->param('query')) || '';
	 $data_source = $CONFIG{'data_source'};
	 
	my $text = qq{
			<FORM METHOD="POST" ACTION="$CONFIG{'script_url'}">
			<INPUT TYPE="hidden" NAME=do VALUE='browse'>
			<INPUT TYPE="hidden" NAME=table VALUE="$table">
			<INPUT TYPE="hidden" NAME=sort_index VALUE="$index">
			<INPUT TYPE="hidden" NAME=action VALUE="$action">
			<INPUT TYPE="hidden" NAME=fields VALUE="$fields">
			<INPUT TYPE="hidden" NAME=where VALUE="$where">
			<INPUT TYPE="hidden" NAME=example VALUE="$example">
			<INPUT TYPE="hidden" NAME=query VALUE="$query">
			Goto Page: <INPUT TYPE="text" NAME=page VALUE = "" SIZE="10"> of $pages
			<INPUT TYPE="submit" value=" Go "><P></FORM>};
 return $text;
}
sub html_table_select{
 my ($in, $select_table, $example_table) = @_;
my ($text,$do,$home_url,$script_url,$data_source,$db,$table,$help_topic,$version);
  									$do              = scalar $in->param('do');
                                    $home_url        = $CONFIG{'home_url'};
                                    $script_url      = $CONFIG{'script_url'}; 
                                    $data_source     = $CONFIG{'data_source'};
                                    $db              = &get_db($CONFIG{'data_source'});
                                    $table           = scalar $in->param('table');
                                    $help_topic      = "select";
                                    $version         = $VERSION;
 $text = qq{<HTML>
			<HEAD><TITLE>
			DB2Man: Search
			</TITLE></HEAD>
			<BODY BGCOLOR="#CCCCCC">
			<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
						<tr><td bgcolor="navy">
								<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
								<b>DB2Man: Search</b>
						</td></tr>
						<tr><td>};
#<%include header.txt%>
	$text .= &html_header($in);
	$text .=	qq{<UL>

				<table bgcolor="#FFFFCC" border=1 cellpadding=5 cellspacing=3>
				<td>
				<FORM METHOD="POST" ACTION="$script_url">
				<INPUT TYPE="hidden" NAME=do VALUE='browse'>
				<INPUT TYPE="hidden" NAME=table VALUE="$table">
				<INPUT TYPE="hidden" NAME=page VALUE=1>
				<INPUT TYPE="hidden" NAME=action VALUE='select'>
				<B>SELECT:</B>
				$select_table
				<P>
				<B>Where: </B><BR><TEXTAREA NAME="where" ROWS="3" COLS="30" VALUE= ""></TEXTAREA>
				<P>
				<B>Do a "query by example" (wildcard: "%"):</B><BR>
				$example_table
				<P>
				<INPUT TYPE="submit" value=" Go "></FORM>
				</td></table>

				</UL>
				</td></tr></table>
				</BODY></HTML>};

 print $text;

}
sub html_table_browse{
my($in, $table, $page_jump, $page_link, $col_name, $table_records, $query, $empty_set, $pri_key, $query_printed, $total_rec_num, $save_search_link) = @_;
 my $from_monitor = scalar $in->param('from_monitor');
 my $text;


 $text = qq{<HTML>
<HEAD><TITLE>
DB2Man: View Table $table
</TITLE></HEAD>
<BODY BGCOLOR="#CCCCCC">
<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
			<tr><td bgcolor="navy">
					<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
                    <b>DB2Man: View Table $table</b>
			</td></tr>
			<tr><td>};
 $text .= &html_header($in);
#<%include header.txt%>

if ($from_monitor){
$text .= qq{<UL>
<P>
<FORM METHOD="POST" ACTION="$CONFIG{'script_url'}">	
	<B>* Run SQL query/queries</B><BR>
	<INPUT TYPE="hidden" NAME=do VALUE='sql_monitor'>
	<INPUT TYPE="hidden" NAME=action VALUE="monitor">
	<INPUT TYPE="hidden" NAME=from_monitor VALUE="1">
	<TEXTAREA NAME="query" ROWS="7" COLS="40" VALUE= ""></TEXTAREA><BR>
	<INPUT TYPE="submit" value=" Go ">
</FORM>
<P>};
if ($total_rec_num){
 $text .=qq{$total_rec_num rows affected };
}
 $text .= qq{</UL>};
}

if (!$from_monitor){
$text .= qq{<TABLE BORDER=0 WIDTH=60% >
<TR><TD><span style="cursor:hand" onMouseover="query.style.display='block'"
  onMouseout="query.style.display='none'"> SQL-query</span></TD></TR>
<TR id="query" style="display:none;cursor:hand;border:0.5px solid blue;" onMouseover="this.style.display='block'"
  onMouseout="this.style.display='none'"><TD>($query_printed) </TD></TR>
</TABLE>
<P>};
if ($total_rec_num){
 $text .= qq{( $total_rec_num records in total )  <a href="$save_search_link">Save Result</a>};
 }
}


 $text .=	$page_jump;
 $text .=	$page_link;
 if($empty_set){
 $text .= qq{<TABLE BORDER = 2 CELLPADDING = 10>
		<TD><B>Empty Set</B></TD>
		</TABLE>};
		}

 if(!$empty_set){
 $text .= qq{<TABLE BORDER=2>
				<TR>
				$col_name};
if( $pri_key){
 $text .= qq{<TD></TD><TD></TD>};
 }
 $text .= qq{</TR>
			$table_records
			</TABLE>};
		}
 $text .=	qq{$page_link
			</td></tr></table>
			</BODY></HTML>};
  print $text;
}

sub message_html{
 my $feedback = shift;
 
  my $text =   qq{<FONT SIZE=2>
		<TABLE BORDER=1 CELLPADDING=3>
		<TR>
			<TD>
			<B><FONT COLOR="#006600">MySQL message:</FONT></B>
			</TD>
		</TR>
		<TR>
			<TD>
			$feedback
			</TD>
		</TR>
		</TABLE>
		</FONT>};
 return $text;
}

sub html_header{
my $in = shift;
my $db = &get_db($in->param('data_source') || $CONFIG{'data_source'});
my $data_source = scalar $in->param('data_source') || $CONFIG{'data_source'};
my $table = scalar $in->param('table') || '';
my $do  = scalar $in->param('do');
my $page = scalar $in->param('page') || 1;
my $help_topic      = 'edit';
my $text = qq{
<table border="1" width="100%" cellspacing="0" cellpadding="2">
  <tr>
    <td width="80%"><b><font face="Verdana, Arial, Helvetica" size="4"><A href="$CONFIG{'script_url'}">Top</A> :
      <A href="$CONFIG{'script_url'}">DB2</A>};
	  if($db){
      $text .= qq{: <A href="$CONFIG{'script_url'}?do=tables">$db</A>&nbsp;};
	  }
      if ($table) {
		if($do ne 'create_table'){
	  $text .= $table;
	  if($page > 1){
		$text .= qq{(page:&nbsp; $page)}; 
				}
			}
		}
    $text .= qq{</td>
				<td width="20%" align="right">
					<font face="Verdana, Arial, Helvetica" size="2">
					<b>Help:</b> 
					<a href="$CONFIG{'script_url'}?do=help&help_topic=home" target="a">Home</a> | 
					<a href="$CONFIG{'script_url'}?do=help&help_topic=$help_topic" target="a">Page</a>
					</font>
				</td>
			</tr>
			<tr>};
    
    if(!$db){
		$text .= qq{<td width="80%" valign=top>};
		}
    if($db){
	     $text .= qq{<td width="80%">};
		 }
		 $text .= qq{<font face="Verdana, Arial, Helvetica" size="2"><b>Databases:</b>
					<A href="$CONFIG{'script_url'}">List</A> 
					  | <A href="$CONFIG{'script_url'}?do=top_level_op&action=create_db">Create</A>};
	if($db){
		  $text .= qq{| <A href="$CONFIG{'script_url'}?do=top_level_op&table=};
		  if($do ne 'create_table'){
		   $text .= $table
		   }
		   $text .= qq{&action=sql_monitor">SQL Monitor</A> 
					  | <A href="$CONFIG{'script_url'}?do=top_level_op&table=};
					  
			 if($do ne 'create_table'){
			 $text .= $table;
			 }
			 $text .= qq{&action=mysqldump">SQL Dump</A>};
			}
		  $text .= qq{| <A href="$CONFIG{'script_url'}?do=login&table=};
		  if($do ne 'create_table'){
		   $text .= $table
		   }
		   $text .= qq{">Login</A>
					  | <A href="<%script_url%>?do=logout">Logout</A> 
					<br>};
			if($db){
				$text	.=qq{<b>Tables:</b> 
					<A href="$CONFIG{'script_url'}?do=tables">List</A> 
		| <A href="$CONFIG{'script_url'}?do=top_level_op&action=create_table">Create</A><br> };
		
				$text	.=qq{<b>Views:</b> 
				<A href="$CONFIG{'script_url'}?do=views">List</A> };
		if ($table) {
		
			if($do ne 'create_table'){
			$text .= qq{| <A href="$CONFIG{'script_url'}?do=browse&table=$table&page=1&action=browse">Browse</A> 
			| <A href="$CONFIG{'script_url'}?do=select&table=$table&page=1&action=select">Search</A> 
			| <A href="$CONFIG{'script_url'}?do=property&table=$table">Properties</A> 
			| <A href="$CONFIG{'script_url'}?do=insert&table=$table">Insert</A> 
			| <A href="$CONFIG{'script_url'}?do=modify&table=$table&action=empty_table&skip_url=1">Empty</A> 
			| <A href="$CONFIG{'script_url'}?do=modify&table=$table&action=drop_table&skip_url=1">Drop</A> 
			| <A href="$CONFIG{'script_url'}?do=top_level_op&table=$table&action=import">Import</A> 
			| <A href="$CONFIG{'script_url'}?do=top_level_op&table=$table&action=export">Export</A> 
			| <A href="$CONFIG{'script_url'}?do=top_level_op&table=$table&action=rename_table">Rename</A> 
			| <A href="$CONFIG{'script_url'}?do=top_level_op&table=$table&action=add_fields">Add_Fields</A>};
			}
		}
     }	
      
     $text .= qq{ </font></td>
    <td width="20%">
      <p align="right"><span><font face="Verdana, Arial, Helvetica" size="1">DB2Man based on&nbsp;&nbsp;</font></span><a href="http://www.gossamer-threads.com/scripts/"><font face="Verdana, Arial, Helvetica" size="1">MySQLMan
      v. $VERSION<br>
      © 2000 Gossamer Threads Inc.</font></a></td>
  </tr>
</table>
<P>};

return $text;


}

sub html_save_search {

	my $in = shift;
	my($text,$do,$home_url,$script_url,$data_source,$db,$table,$insert_fields,$record_modify,$page,$action,$sort_index,$fields,
	   $where,$example,$browse_action,$help_topic,$version,$query);
	$do = $in->param('do');
    $home_url = $CONFIG{'home_url'};
    $script_url = $CONFIG{'script_url'}; 
    $data_source = $CONFIG{'data_source'};
    $db =&get_db($CONFIG{'data_source'});
    $table = scalar $in->param('table');
    $insert_fields = $insert_fields;
    $record_modify = scalar &html_escape($in->param('record_modify'));
    $page = scalar $in->param('page') || 1;
    $action = scalar $in->param('action');
    $sort_index = scalar &html_escape($in->param('sort_index'));
    $fields = scalar &html_escape($in->param('fields'));
    $where  = scalar &html_escape($in->param('where')); 
    $example = scalar &html_escape($in->param('example'));
    $browse_action = scalar $in->param('browse_action');
    $help_topic = 'save_search_result';
    $version = $VERSION;
	$query = scalar &html_escape($in->param('query')) ;
	
$text .=qq{<HTML>
<HEAD>
<TITLE>Save Search Result</TITLE>

</HEAD>
<BODY BGCOLOR="#CCCCCC">
<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
			<tr><td bgcolor="navy">
					<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
                    <b>Save Search Result</b>
			</td></tr>
			<tr><td>};
$text .= &html_header($in);
#<%include header.txt%>
$text .= qq{<UL>
			<table bgcolor="#FFFFCC" border=1 cellpadding=5 cellspacing=3>
			<td>
			<li><B> Save Search Result:</B><BR>
				<UL>
					<FORM METHOD="POST" ACTION="$script_url" name="ExportForm">
					<INPUT TYPE="hidden" NAME=do VALUE='export'>
					<INPUT TYPE="hidden" NAME=table VALUE="$table">
					
					<INPUT TYPE="hidden" NAME=action VALUE="$browse_action">
					<INPUT TYPE="hidden" NAME=page VALUE="$page">
					<INPUT TYPE="hidden" NAME=sort_index VALUE="$sort_index">
					<INPUT TYPE="hidden" NAME=fields VALUE="$fields">
					<INPUT TYPE="hidden" NAME=where VALUE="$where">
					<INPUT TYPE="hidden" NAME=example VALUE="$example">
					<INPUT TYPE="hidden" NAME=from_save_result VALUE="1">
					<INPUT TYPE="hidden" NAME=query VALUE="$query">

					<input type="radio" name="export_to_screen" value="1" CHECKED> <B>Print to screen.</B><BR>
					<input type="radio" name="export_to_screen" value="0"> <B>Export to file.&nbsp;&nbsp;
					Path: </B><INPUT TYPE="text" NAME="file" VALUE="" SIZE="45"><P>

					<B>Options:</B><BR>
					Fields:
					<UL>
					Delimiter: <INPUT TYPE="text" NAME="delimiter" VALUE="|" SIZE="2"><BR>
					Escape Character: <INPUT TYPE="text" NAME="escape_char" VALUE="\" SIZE="2"><BR>
					</UL>
					Records:
					<UL>
					Delimiter: <INPUT TYPE="text" NAME="rec_del" VALUE="\n" SIZE="3"><BR>
					</UL>
					<P>
					<INPUT TYPE="submit" value=" Save ">
					</FORM>
				</UL>
			</td></table>

			</UL>
			</td></tr></table>
			</BODY>
			</HTML>};
			
	print $text;
}

sub html_insert{
	my $in = shift;
	my($text,$do,$home_url,$script_url,$data_source,$db,$table,$insert_fields,$feedback,$help_topic,$version);
	
		$do 			 = $in->param('do');
		#print "testing html_insert\n";
		$home_url  		 = $CONFIG{'home_url'};
		$script_url		 = $CONFIG{'script_url'};
		$data_source  	 = $CONFIG{'data_source'};
		
		$db 			 = &get_db($CONFIG{'data_source'})|| '';
		$table    		 = $in->param('table');
		
	 my $form_fields     = &form_fields($in, 0, ()) or return;
		$insert_fields   = $form_fields;
		$feedback 		 = &html_escape($feedback);
		$help_topic      = "insert";
		$version         = $VERSION;
		
		$text =	qq{<HTML>
			<HEAD><TITLE>
			DB2Man: Insert New Record to Table $table
			</TITLE></HEAD>
			<BODY BGCOLOR="#CCCCCC">
			<table border=1 bgcolor="#FFFFFF" cellpadding=5 cellspacing=3 width="100%" align=center valign=top>
						<tr><td bgcolor="navy">
								<FONT FACE="MS Sans Serif, arial,helvetica" size=1 COLOR="#FFFFFF">
								<b>DB2Man: Insert New Record to Table $table</b>
						</td></tr>
						<tr><td>};
			$text .= &html_header($in);
			#<%include header.txt%>
			$text .= qq{<UL>};
			if ($feedback){
			$text .= &message_html($feedback);
			#<%include message.txt%>
			$text .= qq{<P>};
			}
			$text .= qq{<FORM METHOD="POST" ACTION="$script_url">
			<INPUT TYPE="hidden" NAME=do VALUE='insert_record'>
			<INPUT TYPE="hidden" NAME=table VALUE="$table">
			<table>
			<TD bgcolor="#FFFFCC">
			$insert_fields
			<TD>
			</table>
			<P>
			<INPUT TYPE="submit" value=" Go ">
			</FORM>
			</UL>
			</td></tr></table>
			</BODY></HTML>};

			print $text;
}

sub import_record{
# ---------------------------------------------------
# Import records to the table specified from a delimited 
# text file.
# It is disabled in demo mode.

    my $in = shift;
    my $delimiter       = defined ($in->param('delimiter')) ? $in->param('delimiter') : '';
    my $rec_del         = defined ($in->param('rec_del')) ? $in->param('rec_del') : '';
    my $table           = $in->param('table')       || '';
    my $file            = $in->param('server_file')     || '';
    my $import_all_cols = $in->param('import_all_cols') || '';
    my $local           = $in->param('local')       || '';
    my $replace_op      = $in->param('replace_op')  || '';
    my $replace_act     = $in->param('replace_act') || '';
    my $escape_char     = defined ($in->param('escape_char')) ? $in->param('escape_char') : '';
    my $ignore_line     = $in->param('ignore_line') || 0;

    my @select_fields = $in->param('ImportRight');

    my ($query, $sth, $file_q, $delimiter_q, $rec_del_q, $escape_char_q, $field_op);


	$DBH = &connect_db($in) or return;

    if (!$file) {
        $file = &create_temp_file($in) or return;
    }

    # quote the inputs
    $file_q        = $DBH->quote($file);
    $delimiter_q   = "'" . $delimiter . "'";
    $rec_del_q     = "'" . $rec_del . "'";
    $escape_char_q = $DBH->quote($escape_char);

    if (!$replace_op) { $replace_act = ''; }
 # TODO
 # Change to DB2 Syntax
    $query = qq~LOAD DATA $local INFILE $file_q $replace_act
                INTO TABLE $table
                FIELDS
                    TERMINATED BY $delimiter_q
                    ESCAPED BY $escape_char_q
                LINES TERMINATED BY $rec_del_q
                IGNORE $ignore_line LINES~;
    
    if (!$import_all_cols) {  # import selected fields only.
        my $selected_cols = "(" . join("," , @select_fields) . ")";
        $query .= " $selected_cols"; 
    }

    $sth = &exec_query($query) or return;
    $sth->finish();

    if ($in->param('upload_local_file') && !$in->param('server_file')) {
        unlink $file;
    }

    &show_tables($in, "File Imported Successfully.");
}

sub export_record{
# ---------------------------------------------------
# Exort records from the table specified and produce a 
# delimited text file.
# It is disabled in demo mode.

    my $in = shift;
    my $export_all_cols = $in->param('export_all_cols') || '';
    my $delimiter       = $in->param('delimiter');
    my $rec_del         = defined ($in->param('rec_del')) ? $in->param('rec_del') : '';
    my $table           = $in->param('table') || '';
    my $file            = $in->param('file') || '';
    my $escape_char     = defined ($in->param('escape_char')) ? $in->param('escape_char') : '';
    my $to_screen       = $in->param('export_to_screen') || '';
    if ($to_screen && $file eq '') { $file = &get_temp_file_name($table); }

    my ($query, $sth, $file_q, $delimiter_q, $rec_del_q, $escape_char_q, $cols);

    my @select_fields = $in->param('ImportRight');


    if (!$to_screen && !$file) {
        &sqlerr("Please provide a file name for export.");
        return;
    }

    $DBH = &connect_db or return;

    # quote the parameters.
	if($delimiter eq '') {$delimiter = "\t";}
    $file_q        = $DBH->quote($file);
    $delimiter_q   = $DBH->quote($delimiter);
    $rec_del_q     = "'" . $rec_del . "'";
    $escape_char_q = $DBH->quote($escape_char);

    if ($export_all_cols) { # select all fields
        $cols = '*'
    }
    else{ # export selected fields only.
        $cols = join("," , @select_fields);
    }
    
    if ($in->param('from_save_result')) {

        my $fields = $in->param('fields');
        my $action = $in->param('browse_action');

        if ($action eq 'browse') {
           # $query = qq~SELECT *
           #             INTO OUTFILE $file_q 
           #             FIELDS
           #                 TERMINATED BY $delimiter_q
           #                 ESCAPED BY $escape_char_q
           #             LINES TERMINATED BY $rec_del_q
           #             FROM $table~; 
			$query = qq{SELECT * FROM $table};
        }
        else {
            
            my $where_clause = '';
            my $where   = $in->param('where');
            my $example = $in->param('example');

            if ($where) { $where_clause = "WHERE $where"; }

            # Query by example.
            if ($example) {
                if ($where_clause) { $where_clause .= " AND $example"; }
                else { $where_clause = "WHERE $example"; }
            }
            
            # $query = qq~SELECT $fields
            #            INTO OUTFILE $file_q 
            #            FIELDS
            #                TERMINATED BY $delimiter_q
            #                ESCAPED BY $escape_char_q
            #            LINES TERMINATED BY $rec_del_q
            #            FROM $table 
            #            $where_clause~;
			$query = qq{SELECT * FROM $table
						$where_clause};
        }
    }
    else{
        #$query = qq~SELECT $cols
        #            INTO OUTFILE $file_q 
        #            FIELDS
        #                TERMINATED BY $delimiter_q
        #                ESCAPED BY $escape_char_q
        #            LINES TERMINATED BY $rec_del_q
        #            FROM $table~;
		$query = qq{SELECT $cols FROM $table};
    }
    $sth = &exec_query($query) or return;
	# Delete file if it exists
	unlink $file;
	open(TEMP,">>".$file) or die print "\nerror open file ".$file,$!,"\n";
	while(my @record = $sth->fetchrow_array()){
	print TEMP join($delimiter,@record),"\n";
	}
	close TEMP;

    $sth->finish();

    if ($to_screen) {        
        print "<pre># Exported data from table $table\n";
        print "# A temporary file ($file) was create in the temp directory.\n";
        print "# Please remove the file manually as necessary.\n\n";
        print "# =========== Export Starts ===========\n";
		#delete file if it exists
		#unlink $file;
        open (TEMP, $file) or die print "\nerror open file ".$file,$!,"\n";
        while (my $line = <TEMP>) {
            print $line;
        }
        close TEMP;
        print "\n# =========== Export Ends ===========</pre>";

		if($to_screen){
        #unlink($file);
		}
        return 1;
    }
    elsif ($in->param('from_save_result')){
        &table_browse($in);
    }
    else{
        return &show_tables($in, "File Exported Successfully.");
    }
}

sub create_temp_file{
# ---------------------------------------------------
# creates a temp file and return the path to the file.

    my ($in) = @_;
    my $temp_file = &get_temp_file_name();
    my $fh = $in->param('upload_local_file') || '';
    
    if (!$fh) { &sqlerr('Query file not specified.'); return;}

    if (!open(OUTFILE, ">$temp_file")) {
      &cgierr("There was an error opening temp file '$temp_file' for writing.\n");
    }

    open (OUTFILE,">>$temp_file");
    my ($buffer);
    while (read($fh,$buffer,1024)) {
        print OUTFILE $buffer;
    }

    close($fh);
    close(OUTFILE);
    #chmod (0666, "$temp_file");

    return $temp_file;
}

sub form_fields{
# ---------------------------------------------------
# Create a form input table for insert and edit.  $update
# is a flag indicating whether or not it is from edit.  @value 
# consists the list of original values (in order) in the 
# record being updated.  Note that in order to set a field
# to be null, the input value has to be null.  In other words, 
# if there is value in input field and null checkbox is checked, 
# the null option will be overwritten and the value in the input 
# field will be taken.
#
# Option: you can set it in the config file such that any colume 
# with type TIMESTAMP will not be shown in the form.

    my($in, $update, @value) = @_;
    
    my $table = $in->param('table') || '';
    my ($query, $sth, $form_table, @ary, $type, @domain, @domain_new, %domain_h, $value_unquote,
        $flag, $double_comma, $length_set,$nullable,$colname);

	my @timestamp_hidden = ();
   #print "testing\n";
    $DBH = &connect_db($in) or return; 
     #DB2 way to get table information
	 $query = "SELECT * FROM ".$table." FETCH FIRST ROW ONLY";
    #$query = "SELECT COLNAME,TYPENAME,LENGTH,SCALE,NULLS from syscat.columns where tabname='".$table."'";
    $sth = &exec_query($query) or return; 

    $form_table = "<TABLE BORDER = 2><TR><TH>Fields</TH><TH>Type</TH><TH>Function</TH><TH>Value</TH>";
    if ($CONFIG{'insert_null'}) { $form_table .= "<TH>Null</TH></TR>"; }
    else {$form_table .= "</TR>";}

    my $k = 0; # Value counter.  Used to identify which element in @value is considered.
    for (my $i = 0; $i < $sth->{NUM_OF_FIELDS};$i++){
    #while (@ary = $sth->fetchrow_array) {
    my $tabindex_count = $k+1;
		#print Dumper($DBH);
        # use statement handle to aquire properties of query.
        #$type =  $DBH->type_info($sth->{TYPE}->[$i])->{TYPE_NAME};
		$type = $DB2_TYPES{$sth->{TYPE}->[$i]};
		#print $type;
		$nullable = $sth->{NULLABLE}->[$i];
		$colname  = $sth->{NAME}->[$i];
        $length_set = $sth->{SCALE}->[$i];
		
        #for (my $j=2; $j <= $#type; $j++) {$length_set .= $type[$j];}
        chop $length_set;
        #print $length_set,"\n";
    
        # Handle type 'Enum'        
        if ($type eq 'enum') {
            $form_table .=  qq~\n<TR><TD>$ary[0]</TD><TD>enum</TD><TD>~ . &function_select($ary[0]) . qq~</TD><TD><select name="*insert*_$ary[0]" tabindex="$tabindex_count">~;

            #if (defined($value[$k]) && $update) { 
            #    $form_table .= qq~\n<option>$value[$k]</option>~; 
            #}

            # Create an empty choice.  This choice available even if it is not specified in 
            # enum.  We need it in case the value needs to be null.
            $form_table .= qq~\n<option></option>~;
        
            
            # All other choices in specified in the enumeration.
            #$type = &parse_length_set($length_set);

            #for (my $i=0; $i <= $#type; $i++) {
                if (defined($type) && $type ne "''" && $type ne '') {
                    ($value_unquote) = $type =~ m{^\'(([^\']|\'\')+)\'};
                    # Since MySQL stores single quotes in 2 single quotes in column specs,
                    # we translate them back to 1. 
                    $value_unquote =~ s/''/'/g;
                    $value_unquote =~ s/\\\\/\\/g;
                    $form_table .= qq~\n<option>$value_unquote</option>~;
                }
            #}
            # Null checkbox
            if ($CONFIG{'insert_null'}) {
                if ($nullable ==1) { 
                    if ( !defined($value[$k]) && $update) { $form_table .= qq~</select></TD><TD><input type="checkbox" name="*insert*_~.$nullable. qq~_null" value="NULL" checked></TD></TR>~; }
                    else {$form_table .= qq~\n</select></TD><TD><input type="checkbox" name="*insert*_~.$nullable.qq~_null" value="NULL"></TD></TR>~; }
                }
                else { $form_table .= qq~\n</select></TD><TD></TD></TR>~; }
            }
        }

        # Handle type 'Set'
        elsif($type eq 'set'){
        
            my $j = 0;

            $form_table .= qq~\n<TR><TD>$colname</TD><TD>set</TD><TD>~ . &function_select($colname) . qq~</TD><TD>~;
            
            # For update, check if '' is in the set.
            @domain = split /(,)/, $value[$k];
            foreach (@domain) { 
                if ($_ ne ',') { 
                    if ($_ ne '') {push (@domain_new, $_) }
                    else {push (@domain_new, "''")}
                }
            }
            if ($domain[$#domain] eq ',') { push (@domain_new, "''"); }
            %domain_h = map{$_ => 1} @domain_new;

            #@type = &parse_length_set($length_set);         
            
           # for (my $i=0; $i <= $#type; $i++) {
                
                if (defined($type) && $type ne '') {
                    
                    if ($type ne "''") { ($value_unquote) = $type =~ m{^\'(([^\']|\'\')+)\'}; }
                    else { $value_unquote = $type; }
                    
                    if ($value_unquote ne "''") { $value_unquote =~ s/''/'/g; }
                    $value_unquote =~ s/\\\\/\\/g;
                    
                    # Create checkboxes for each element in the set.  Checkboxes are checked if 
                    # value is selected in the original set.
                    if ($domain_h{$value_unquote}){
                        $form_table .= qq~\n<input type="checkbox" name="*insert*_~ . $colname . qq~_set_$j" value="~ . &html_escape($value_unquote) . qq~" checked tabindex="$tabindex_count">$value_unquote<BR>~;
                        $j++;
                    }
                    else {
                        $form_table .= qq~\n<input type="checkbox" name="*insert*_~ . $colname . qq~_set_$j" value="~ . &html_escape($value_unquote) . qq~" tabindex="$tabindex_count">$value_unquote<BR>~;
                        $j++;
                    }
                }
           # }
            if ($CONFIG{'insert_null'}) {
                if ($ary[4] eq 'Y') { 
                    if ( !defined($value[$k]) && $update) {$form_table .= qq~</TD><TD><input type="checkbox" name="*insert*_~ . $colname . qq~_null" value="NULL" checked></TD></TR>~; }
                    else{$form_table .= qq~\n</TD><TD><input type="checkbox" name="*insert*_~ . $colname . qq~_null" value="NULL"></TD></TR>~;}
                }
                else { $form_table .= qq~</TD><TD></TD></TR>~; }
            }
        }

        # Handle all other types
        else {
			my $type_lookup   = lc($type);
			#print $type_lookup."\n";
			my $hidden_field  = '';

			# hide columns with type TIMESTAMP if necessary.
			if (($type_lookup =~ m/timestamp/) && !$CONFIG{'show_timestamp_field'}) {  
				if (!$update) {
					$hidden_field = qq~<INPUT TYPE="hidden" NAME="*insert*_~ . $colname . qq~_null" VALUE="NULL">~;
					push (@timestamp_hidden, $hidden_field);
				}
				else{
					$hidden_field = qq~<INPUT TYPE="hidden" NAME="*insert*_~ . $colname . qq~" VALUE="~ . &html_escape($value[$k]) . qq~">~;
					push (@timestamp_hidden, $hidden_field);
				}
			}
			else{
				# handle fields with type TEXT or BLOB.  
				if ($type_lookup =~ m/text/ || $type_lookup =~ m/blob/) {
					$form_table .= qq~\n<TR><TD>$colname</TD><TD>$type</TD><TD>~ . &function_select($colname) . qq~</TD><TD><TEXTAREA NAME="*insert*_~.$colname.qq~" ROWS="5" COLs="30" WRAP="VIRTUAL" tabindex="$tabindex_count">~ . &html_escape($value[$k]) . qq~</TEXTAREA></TD>~; 
				}
				else{
				   #printf "Colname %s value %s<br>",$colname,$value[$k];
		            $form_table .= qq~\n<TR><TD>$colname</TD><TD>$type</TD><TD>~ . &function_select($colname) . qq~</TD><TD><INPUT TYPE="text" NAME="*insert*_~.$colname. qq~" VALUE="~ . &html_escape($value[$k]) . qq~" SIZE="30" tabindex="$tabindex_count"></TD>~; 
				}
	            if ($CONFIG{'insert_null'}) {
	                if ($nullable==1) { 
	                    if ( !defined($value[$k]) && $update) {$form_table .= qq~<TD><input type="checkbox" name="*insert*_~ . $colname . qq~_null" value="NULL" checked></TD></TR>~; }
	                    else { $form_table .= qq~<TD><input type="checkbox" name="*insert*_~ . $colname . qq~_null" value="NULL"></TD></TR>~; }
	                }
	                else { $form_table .= qq~<TD></TD></TR>~; }
	            }
			}
        }
        $k++;
    }
    $form_table .= "</TABLE>";
    $sth->finish();
    
	if (@timestamp_hidden) {
		$form_table .= join("", @timestamp_hidden);
	}

    return $form_table;
}
# ===================== #
#   Insert New Record   #
# ===================== #

sub insert_record{
# ---------------------------------------------------
# This function insert a new record into the table specified.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $feedback;
    my ($query, $sth, @insert_info, $new_record, @insert_fields, $fields, @insert_values, $values);


    $DBH = &connect_db($in) or return;
    
	# Get the info of the new record to be inserted.
    @insert_info = &compose_new_condition($in, 1);
   if($#insert_info < 2){
    # No values when submitted. Need to pass error back
    my $text .= &html_header($in);
    $text .= qq{<p>Please return back and enter data</p>
	             <button onclick="window.history.back();">Go Back</button>};
    print $text;
    return;
    }

	my $counter = 0;
	foreach my $element (@insert_info) {
		
		my $is_value = $counter % 2;

		if ($is_value) { # Get the values
			push (@insert_values, $element)
		}
		else { # Get the name of the fields
			push (@insert_fields, $element)
		}
		$counter++
	}

	# Make the input from the form into a string to fit in the query.
    $fields = join ",", @insert_fields;
	$values = join ",", @insert_values;

    $query = "INSERT INTO $table ($fields) VALUES ($values)";  
    $sth = &exec_query($query) or return;
    $sth->finish();
    
    $feedback = 'Record Inserted.';
    if ($CONFIG{'insert_origin'} eq 'table') { &show_tables($in, $feedback); }
    else { &html_insert($in, $feedback) }
}

sub function_select {
# ---------------------------------------------------
# Creates enumeration of functions available in select input.

    my $field = shift;
	
	my $text = "<select name=*insert*_".$field."_function><option>
						<option>ASCII
						<option>CHAR
						<option>SOUNDEX
						<option>CURDATE
						<option>CURTIME
						<option>FROM_DAYS
						<option>FROM_UNIXTIME
						<option>NOW
						<option>PASSWORD
						<option>PERIOD_ADD
						<option>PERIOD_DIFF
						<option>TO_DAYS
						<option>USER
						<option>WEEKDAY
						<option>RAND
						</select>";
    return $text;
}
sub valid_name_check{
# ---------------------------------------------------
# Checks to see if the input database/table name is a 
# valid one.  The function checks the following:
# 1. if a name is entered at all;
# 2. if there are spaces in the name;
# 3. if the name is consisted of valid characters; and
# 4. if the name is consisted of only numbers.

    my $name = shift;

    $name =~ s/^\s+//;  
    $name =~ s/\s+$//;

    my @name = split / /, $name;

    if (!$name)                 { &sqlerr("Please provide a valid name."); }
    elsif ($#name > 0)          { &sqlerr("Spaces are not allowed in name."); }
    elsif ($name =~ m/[^\w_\$]/){ &sqlerr("Invalid name.  A name may consist of characters, numbers, and also '_' and '\$'."); }
    elsif (!($name =~ m/\D/))   { &sqlerr("Invalid name.  A name may not consist only of numbers."); }
    else  {return 1;}
}
sub compose_new_condition{
# ---------------------------------------------------
# Reconstructs the input from "sub form_fields" to an array
# of "field = value" pairs.
#
# The functions is modified after v1.03
# The way that the script inserts a record is changed to
#
# INSERT INTO tablename (column1,column2,...columnn)
# VALUES (value1,value2, .. valuen)
#
# as the SET col=val isn't supported by all versions of mysql.
# Therefore, if is_insert flag in on, the function returns
# a array in the following format:
#
# (field_name_1, value_for_field_name_1, field_name_2, value_for_field_name_2, ...)
#
# Please note that the value in $value is quoted.
#

    my ($in, $is_insert) = @_;
    my $table = $in->param('table') || '';
    my ($query, $prep, $sth, @ary, $value, @insert_fields, $type, @set, $new_record, $value_unquote);


    #$query = "DESCRIBE $table";
    $query = "SELECT COLNAME,TYPENAME,LENGTH,SCALE,NULLS from syscat.columns where tabname='".$table."'";
    $prep = &exec_query($query) or return;

    while (@ary = $prep->fetchrow_array) {
        
        $type =  $ary[1];
    
        # Handle columns of type 'SET'
        if ($type eq 'set') {            
           # my $j = 0;  # checkbox counter
           #my $k = 0;  # counter for how many checkboxes are checked.
            
            # check each checkbox box to see if they are check.
            #for (my $i=1; $i < ($#type + 1); $i++) {
            #    ($value_unquote) = $type[$i] =~ m{^\'(([^\']|\'\')+)\'};                
            #    if (defined($type[$i])) {
            #        if ( defined($in->param("*insert*_$ary[0]_set_$j")) ) {
            #            if ( $in->param("*insert*_$ary[0]_set_$j") ne "''" ) { push (@set, $in->param("*insert*_$ary[0]_set_$j") ); }
            #            else { push (@set, ''); }
            #            $k++;
            #        }
            #    $j++;
            #    }
            #}






            #$value = $DBH->quote( join(",", @set) );
            
            ## If none of the checkboxes is checked, check for null option. 
            #if (!$k) {
            #    if ($in->param("*insert*_$ary[0]_null")) { $value = 'NULL'; }
            #    else { $value = '""'; }
            #}

        }
        # Handle all other types.
        else {
            # if nothing in input field.
            if (!$in->param("*insert*_$ary[0]") && ($in->param("*insert*_$ary[0]") ne '0')) {
                
                # check for null
                if ($in->param("*insert*_$ary[0]_null")) { $value = 'NULL'; }               
                
                # check for function.
                else { 
                    if ( $in->param("*insert*_$ary[0]_function") ) {$value = $in->param("*insert*_$ary[0]_function") . '()'; }  
                    else { $value = ''; }
                }
            }

            # check if any function is needed to apply on the input.
            elsif ($in->param("*insert*_$ary[0]_function")){ 
                $value = $in->param("*insert*_$ary[0]_function") . '(' . $DBH->quote($in->param("*insert*_$ary[0]")) .')'; 
            }

            # otherwise make the field equal to the value entered.
            else{ $value = $DBH->quote($in->param("*insert*_$ary[0]")); }
        }
		if ($is_insert) {
          if($value ne ''){
			push (@insert_fields, $ary[0]);
			push (@insert_fields, $value);
           }
		}
		else{
	        push (@insert_fields, "$ary[0] = $value");  
		}
    }
    $prep->finish();
	#print '@insert_fields = ', dump(@insert_fields),"\n";
    return (@insert_fields);
}

sub parse_length_set{
# ---------------------------------------------------
# A simple parser that gets each element in the length set field. 
# Basically, it counts the number for sigle quotes.  Each element 
# must have even number of quotes.  If a comma encountered, then 
# the check the number for quotes seen so far.  If the number is odd, 
# then concate the comma to temp string, otherwise, push the current 
# tmep string to array.

    my ($length_set) = @_;

    my @type = split /([,'])/, $length_set;  # list of quoted elements in length_set
    my @new_type = ();
    my $remainder = 0;
    my $cur_choice = '';
    my $q_count = 0;
    my $begin = 0;
    my $k = 0;

    foreach my $element (@type) {
        if ($k == $#type) { 
            $cur_choice .= $element;
            push(@new_type, $cur_choice); 
        }
        elsif ($element ne '') {            
            if ($element eq ',') {
                $remainder = $q_count%2;
                if ($remainder) {
                    if ($begin) {
                        push(@new_type, $cur_choice);
                        $begin = 0;
                        $q_count = 0;
                        $cur_choice = '';
                    }
                    else{
                        $begin = 1;
                        $cur_choice .= $element;
                        $q_count = 0;
                    }
                }
                else{
                    if ($begin) {
                        $cur_choice .= $element;
                    }
                    else {
                        push(@new_type, $cur_choice);
                        $q_count = 0;
                        $cur_choice = '';
                    }
                }   
            }
            elsif($element eq "'"){
                $q_count++;
                $cur_choice .= $element;
            }
            else{
                $cur_choice .= $element;
            }
        }
        $k++;
    }
    return @new_type;
}

# ====================== #
#    Table Alteration    #
# ====================== #

sub alter_table{
# ---------------------------------------------------
# Identify alter table action.

    my $in = shift;
    my $action = $in->param('action') || '';

    if      ($action eq 'alter_col')    { &alter_col_html($in); }
    elsif   ($action eq 'do_alter_col') { &alter_col($in); }
    elsif   ($action eq 'drop_col')     { &drop_col($in); }
    elsif   ($action eq 'set_primary')  { &set_primary($in); }
    elsif   ($action eq 'set_index')    { &set_index($in); }
    elsif   ($action eq 'set_unique')   { &set_unique($in); }
    elsif   ($action eq 'drop_key')     { &drop_key($in); }
    elsif   ($action eq 'add_col')      { &add_col($in);}
    elsif   ($action eq 'rename_table') { &rename_table($in);}
    else    { &cgierr("Alter Table action cannot be idenfied"); }
}

sub alter_col_html{
# ---------------------------------------------------
# The function first reads in the spec's of the column 
# chosen in the current table.  Then the type/length_set
# /attribute is identified individually.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $col = $in->param('col')     || '';

    my ($field, $type, $null, $key, $default, $extra);
    my ($sth, $query, $length_set, $attributes, $dump, $type_name);

    
    # Get column specification.
    $DBH = &connect_db($in) or return; 
    $col = $DBH->quote($col);
    $query = "SHOW COLUMNS FROM $table LIKE $col";
    $sth = &exec_query($query) or return;
    
    # parse column definition.
    my @ary = $sth->fetchrow_array;
    ($field, $type_name, $length_set, $attributes, $null, $key, $default, $extra) = parse_col_spec(@ary);
    $sth->finish();

    &html_alter_col($in, $field, $type_name, $length_set, $attributes, $null, $default, $extra);
}

sub alter_col{
# ---------------------------------------------------
# Updates the column specification.  The input from the 
# alter column is taken in and made into a string to be
# fit as part of the query string.  Then the user is 
# brought back to the property page.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $col = $in->param('col')     || '';
    my ($col_spec, $sth, $query);


    $DBH = &connect_db($in) or return; 

    # Get the updated column specs in string format.
    $col_spec = &concate_col_spec($in, 0);
    
    $query = "ALTER TABLE $table CHANGE $col $col_spec";
    $sth = &exec_query($query) or return;
    $sth->finish();
    
    &table_property($in, "Specification of Column $col of Table $table Has Been Changed.")
}

sub drop_col{
# ---------------------------------------------------
# The function drops the column/field specified 
# if the confirmed flag is on.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $col = $in->param('col')     || '';
    my ($col_spec, $sth, $query);


    $query = "ALTER TABLE $table DROP $col";

    if ( $in->param('comfirmed') ){
        $DBH = &connect_db($in) or return; 
        $sth = &exec_query($query) or return;
        $sth->finish();
        &table_property($in, "Column $col of Table $table Has Been Dropped.");
    }
    else { &html_confirm_action($in, $query); }
}

sub set_primary{
# ---------------------------------------------------
# The function will first set the column not nullable 
# and then set the column as primary key.  Note that an
# error will occur if all there already exists a primary key.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $col = $in->param('col')     || '';
    my ($sth, $query);


    $DBH = &connect_db($in) or return; 
    $query = "ALTER TABLE $table ADD PRIMARY KEY ($col)";
    
    # Set the column not nullable
    &set_col_not_null($in);

    $sth = &exec_query($query) or return;
    $sth->finish();
    
    &table_property($in, "Column $col set as primary key.");
}

sub set_index{
# ---------------------------------------------------
# The function will first set the column not nullable 
# and then set the column as index.  Note that an
# error will occur if all there already exists a primary key.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $col = $in->param('col')     || '';
    my ($sth, $query);

    
    $query = "ALTER TABLE $table ADD INDEX ($col)";

    $DBH = &connect_db($in) or return; 

    # Set the column not nullable.
    &set_col_not_null($in);
    
    $sth = &exec_query($query) or return;
    $sth->finish();
    
    &table_property($in, "Column $col set as index.");
}

sub set_unique{
# ---------------------------------------------------
# The function will first set the column not nullable 
# and then set the column as unique.  Note that an
# error will occur if all there already exists a primary key.

    my $in = shift;
    my $table = $in->param('table') || '';
    my $col = $in->param('col')     || '';
    my ($sth, $query);


    $query = "ALTER TABLE $table ADD UNIQUE ($col)";

   $DBH = &connect_db($in) or return; 

    # Set the column not nullable.
    &set_col_not_null($in);
    
    $sth = &exec_query($query) or return;
    $sth->finish();
    
    &table_property($in, "Column $col set as unique.");
}

sub drop_key{
# ---------------------------------------------------
# Drops the key specified.
    
    my $in = shift;
    my $table = $in->param('table')       || '';
    my $key_name = $in->param('key_name') || '';
    my ($sth, $query);

    
    if ( $key_name eq 'PRIMARY') { $query = "ALTER TABLE $table DROP PRIMARY KEY"; }
    else { $query = "ALTER TABLE $table DROP INDEX $key_name"; }

    $DBH = &connect_db($in) or return; 
    $sth = &exec_query($query) or return;
    $sth->finish();
    
    if ( $key_name eq 'PRIMARY' ) { &table_property($in, "Primary Key of Table $table Has Been Dropped."); }
    else { &table_property($in, "Index $key_name of Table $table Has Been Dropped."); }
}
sub add_col{
# ---------------------------------------------------
# Adds new columns to the table specified.

    my $in       = shift;
    my $table    = $in->param('table')    || '';
    my $position = $in->param('position') || '';
    my (@field_list, $col_spec, @primary_list, @index_list, @unique_list, $fields, $primary, $index, $unique, $sth, $query);


   $DBH = &connect_db($in) or return; 

    for (my $i = 0; $i < $in->param('num_of_fields'); $i++) {

        $col_spec = 'ADD ' . &concate_col_spec($in, $i) . " $position";
        push (@field_list, "$col_spec");
        
        if ( $in->param("primary_$i") ) { push (@primary_list, $in->param("field_$i")); }
        if ( $in->param("index_$i") )   { push (@index_list, $in->param("field_$i")); }
        if ( $in->param("unique_$i") )  { push (@unique_list, $in->param("field_$i")); }

        $position = "After " . $in->param("field_$i");
    }
    
    # elements in @field_list are in the form "ADD field_name field_spec".
    $fields  = join ",", @field_list;
    $primary = join ",", @primary_list;
    $index   = join ",", @index_list;  
    $unique  = join ",", @unique_list;

    $query = "ALTER TABLE $table $fields";

    if ($primary){ $query .= ", ADD PRIMARY KEY ($primary)" }
    if ($index)  { $query .= ", ADD INDEX ($index)" }
    if ($unique) { $query .= ", ADD UNIQUE ($unique)" }
    
    
    $sth = &exec_query($query) or return;
    $sth->finish();
    
    &table_property($in, "Column(s) added to Table $table");
}

sub rename_table{
# ---------------------------------------------------
# Renames the table chosen to a new name specified.
# The name entered will be checked to see if it is a 
# valid one.  If it is, then the table will be renamed
# and the user will be brought back to the table property 
# page.

    my $in = shift;
    my $new_name  = $in->param('table')     || '';
    my $old_table = $in->param('old_table') || '';
    my ($query, $sth, @name);

    &valid_name_check($in->param('table')) or return;


   $DBH = &connect_db($in) or return; 
    $query = "ALTER TABLE $old_table RENAME AS $new_name";
    $sth = &exec_query($query) or return;
    $sth->finish();

    &table_property($in, "Table $old_table Renamed to $new_name.");
}

sub html_escape {
#--------------------------------------------------------------------------------
# Return the string html_escaped.
#
    my $toencode = (defined $_[0] and ((ref $_[0] eq 'GT::CGI') or ($_[0] eq 'GT::CGI'))) ? $_[1] : $_[0];
    return unless (defined $toencode);
    if (ref($toencode) eq 'SCALAR') {
        $$toencode =~ s/&/&amp;/g;
        $$toencode =~ s/</&lt;/g;
        $$toencode =~ s/>/&gt;/g;
        $$toencode =~ s/"/&quot;/g;
    }
    else {
        $toencode =~ s/&/&amp;/g;
        $toencode =~ s/</&lt;/g;
        $toencode =~ s/>/&gt;/g;
        $toencode =~ s/"/&quot;/g;
    }
    return $toencode;
}

sub get_temp_file_name {
# ---------------------------------------------------
# This function creates a random temp file name, looks
# up the temp directory and returns the path to the 
# temp file.
    my $table = shift;
    my $temp_file_path = '';    
    my $directory      = '.';
	my $filedel        = '';
	my $rand_name      = '';
    my @temp_dirs =("/usr/tmp","/var/tmp","C:\\temp","/tmp","/temp","/WWW_ROOT");
    foreach (@temp_dirs) {
        if (-d $_ && -w _) {$directory = $_; last; }
    } 
   print $table,"\n";	
   if ($table ne ''){	
    $rand_name = $table . join "-",(localtime)[4,3,5] ;
	}else{
    $rand_name = "GTMM" . time . $$ . int(rand(1000));
	}
    # while (-e $directory . '/' . $rand_name) {
        # $rand_name = "GTMM" . time . $$ . int(rand(1000));
    # }
	# is the client's OS Windoze?
	if($directory=~/C:/){
	$temp_file_path = "$directory\\$rand_name";
	}else{
    $temp_file_path = "$directory/$rand_name";
	}
    return $temp_file_path;
}

sub table_field_prep{
# ---------------------------------------------------
# Create options for import and export HTML pages.  The
# options are the fields of the table selected.

    my($in) = @_;
    my $table = $in->param('table') || '';
    my $options = '';
    
    $DBH=&connect_db or return;
    my $query = "SELECT * FROM $table FETCH FIRST ROW ONLY";
    my $sth = &exec_query($query) or return;
    for (my $i = 0; $i < $sth->{NUM_OF_FIELDS}; $i++) {
        $options .= qq~<OPTION value="$sth->{NAME}->[$i]">$sth->{NAME}->[$i]</OPTION>\n~;
    }
    $sth->finish();
    return ($options, $sth->{NUM_OF_FIELDS});
}

sub get_db{
# ---------------------------------------------------
# Gets the database name from the data source which is 
# in the format "DBI:mysql:database_name:host"

    my $db = shift;

    my @dsn = split /([:])/, $db;
    $db = $dsn[4]; 
    if ($CONFIG{'direct_connect'}) { $db = $CONFIG{'direct_db'}; }

    return $db;
}

sub get_cols{
# ---------------------------------------------------
# Takes in a table name and return the columns in an ]
# array.

    my ($table) = @_;
    my ($query, $sth,@ary, @cols);
    $DBH=&connect_db or return;
	
    #$query = "SELECT * FROM $table FETCH FIRST ROW ONLY";
	# DB2 syntax
	$query = "SELECT COLNAME,TYPENAME,LENGTH,SCALE,NULLS from syscat.columns where tabname='".$table."'";
	#print $query," get_cols\n";
    $sth = &exec_query($query) or return;
     while (@ary = $sth->fetchrow_array) {
        push (@cols, $ary[0]);
    }
    $sth->finish();
    return @cols;
}
sub get_pri_key{
# ---------------------------------------------------
# Gets the primary key of the table specified.

    my $table = @_;
    my ($sth, $query, @ary, @pri_key);
    #print "get_pri_key() ",$table,"\n";
    @pri_key = ();

	# DB2 primary keys are found in the SYSIBM.SYSCOLUMNS using the following query
		$query = "SELECT TBCREATOR, TBNAME, NAME, KEYSEQ
					FROM SYSIBM.SYSCOLUMNS
					WHERE TBNAME = '".$table."' AND KEYSEQ > 0
					ORDER BY KEYSEQ";
	# MySQL is 'DESCRIBE $table
    # "DESCRIBE $table";
	#print "get_pri_key() query = ",$query,"\n";
    $sth = &exec_query($query) or return;
    while (@ary = $sth->fetchrow_array) {
         push(@pri_key, $ary[2]); 
    }
    $sth->finish();

    return @pri_key;
}
sub record_count{
# ---------------------------------------------------
# Counts to total number of records/rows in the table 
# specified.

    my ($sth, $rows, $query);

    my $tablename = @_;

    $query = "SELECT COUNT(*) FROM $tablename";
    $sth = &exec_query($query) or return;
    $rows = $sth->fetchrow();
    $sth->finish();
    return $rows;
}
sub connect_db{
	#my $in = shift;
    	my ($db, $db_host, $db_port, $username, $password, $message,$data_source);
    	$db='classifieds';
    	$data_source = $CONFIG{'data_source'};
    	$username = 'UMWR484';
    	$password = 'activeX1';
    	
	# connects to mysql.
    $DBH = DBI->connect("$data_source", "$username", "$password", { RaiseError => 0, PrintError => 1, AutoCommit => 1 })
     or print $DBI::errstr;
     return $DBH;
	}
	
sub exec_query{
# ---------------------------------------------------
# Send the input query thru database handler.

    my ($query) = @_;
    my ($sth);
    #print $query ."<br>";
    $DBH = &connect_db or return;
    
    $sth = $DBH->prepare($query) or print "Error in DBH->prepare()\n".$DBI::errstr."\n <P>Query: $query";
    $sth->execute() or print "Error running the query. DB2 said:". $sth ->errstr()."\n<P>Query: $query"; 

    return $sth;
}
 sub sqlerr{
# ---------------------------------------------------
# Error prompt.

    my $in = new CGI;
    my $error = shift;
    my ($message, $init_login);

    $init_login = 0;
    my $db_connection = $in->param("db_for_connection") || '';

    # If access denied, then a login page will be displayed.
    if ($error =~ m/(.ccess denied)/){ 
        $message = "<p>Permission to perform action denied!</p><blockquote>MySQL Said: $error</blockquote><p>Please enter your user name and password";
        my $args = $in->get_hash;
        if (! keys %$args or ($in->param('do') eq 'login')) {
            $message = 'Welcome! Please enter your log-in info.'; 
            $init_login = 1;    
        }
        elsif ($in->param('init_login')){ 
            $message = 'Login failed.  Please enter another hostname/username/password.'; 
            $init_login = 1;
        }
        &html_login ($in, $message, $init_login); 
        if ( $CONFIG{'debug'} ) {&cgierr("debug");}
        return;
    }

    # If connect error, login page is prompted to let the user to enter another 
    # host name.
    elsif (($DBI::errstr =~ m/an't connect to/) || ($DBI::errstr =~ m/Unknown MySQL Server Host/) ) {
        $message = qq~Connection to DB2 failed.
                      The hostname may be different or the server may be down.
                      Please enter a new hostname and try again.~;
        my $args = $in->get_hash;
        if (! keys %$args or ($in->param('do') eq 'login')) {
            $message = 'Welcome! Please enter your log-in info.'; 
            $init_login = 1;    
        }
        elsif ($in->param('init_login')){ 
            $message = 'Login failed.  Please enter another hostname/username/password.';
            $init_login = 1;
        }
        &html_login($in, $message, $init_login);
        if ( $CONFIG{'debug'} ) {&cgierr("debug");}
        return;
    }

    # database specified not existed
    elsif ($DBI::errstr =~ m/(.nknown database)/) { 
        if (!$db_connection) {
            $message = "Connection to MySQL failed.  A database name is needed for connection.";
            &html_login_dbname($in, $message, $init_login);
            if ( $CONFIG{'debug'} ) {&cgierr("debug");}
            return;
        }
        else{
            $message = "Unknown database '$db_connection'.  Please enter another database name.";
            &html_login_dbname($in, $message, $init_login);
            if ( $CONFIG{'debug'} ) {&cgierr("debug");}
            return;
        }
    }

    # display the error message.
    else{
        if ($CONFIG{'debug'}) { 
            &cgierr($error);
        }
        else { 
            html_sqlerr($in, $error); 
            if ( $CONFIG{'debug'} ) {&cgierr("debug");}
            return;
        }
    }
}

sub cgierr{
# --------------------------------------------------------
# Displays any errors and prints out FORM and ENVIRONMENT
# information. Useful for debugging.
#
    my $in;
    eval { $in = new GT::CGI; };
    if (defined $GT::CGI::PRINTED_HEAD) {
        print "Content-type: text/html\n\n" unless ($GT::CGI::PRINTED_HEAD);
    }
    else {
        print "Content-type: text/html\n\n";
    }

    my ($key, $env);
    my ($error, $nolog) = @_;
    print "</td></tr></table>";
    print "</td></tr></table></center></center>";
    if ($CONFIG{'debug'}) {print "<PRE>\n\nDEBUG\n==========================================\n";}
    else {print "<PRE>\n\nCGI ERROR\n==========================================\n";}
    $error    and print "Error Message       : $error\n";
    $0        and print "Script Location     : $0\n";
    $]        and print "Perl Version        : $]\n";
    
    print "\nConfiguration\n-------------------------------------------\n";
    foreach $key (sort keys %CONFIG) {
        my $space = " " x (20 - length($key));
        print "$key$space: $CONFIG{$key}\n";
    }
    if ($in) {
        print "\nCookies\n-------------------------------------------\n";
        print "$CONFIG{'db_user_cookie_name'} : " . $in->cookie($CONFIG{'db_user_cookie_name'});
        print "\n$CONFIG{'db_pass_cookie_name'} : " . $in->cookie($CONFIG{'db_pass_cookie_name'});
        print "\n$CONFIG{'db_host_cookie_name'} : " . $in->cookie($CONFIG{'db_host_cookie_name'});
        print "\n$CONFIG{'url_cookie_name'} :   " . $in->cookie($CONFIG{'url_cookie_name'});
        print "\nquery_1 :   " . $in->cookie('query_1');
        print "\nquery_2 :   " . $in->cookie('query_2');
        print "\nquery_3 :   " . $in->cookie('query_3');
        print "\nquery_4 :   " . $in->cookie('query_4');
        print "\nquery_5 :   " . $in->cookie('query_5');
        print "\nquery_6 :   " . $in->cookie('query_6');
        print "\nquery_7 :   " . $in->cookie('query_7');
        print "\nquery_8 :   " . $in->cookie('query_8');
        print "\nquery_9 :   " . $in->cookie('query_9');
        print "\nquery_10 :   " . $in->cookie('query_10');

        print "\n\nForm Variables\n-------------------------------------------\n";
        foreach $key (sort $in->param) {
           my $space = " " x (20 - length($key));
           print "$key$space: " . $in->param($key) . "\n";
        }
    }
    print "\nEnvironment Variables\n-------------------------------------------\n";
    foreach $env (sort keys %ENV) {
        my $space = " " x (20 - length($env));
        print "$env$space: $ENV{$env}\n";
    }
    print "\nStack Trace \n-------------------------------------------\n";
    my $i = 0;
    while (my ($file, $line, $sub) = (caller($i++))[1,2,3]) {
        print qq!($sub) called from ($file) line ($line)<BR>\n!;
    }
    print "\n</PRE>";
    exit;
}