use strict;
#use warnings;
use DBI;
use DBD::ODBC;


our $DBH = undef;

my $sth = undef;
my($f,$o,$c,$staticSql,$r);

my ($dsn,$infilecsv,$outfilecsv,$sql) = @ARGV;

if (not defined $dsn) {&printhelp;}
if (not defined $infilecsv){&printhelp;}
if (not defined $outfilecsv) {&printhelp;}
if (not defined $sql) {&printhelp;}

 $staticSql=$sql;


 $DBH = &connect_db or return ;


  #delete file if exists
  if(-e $outfilecsv){unlink $outfilecsv;}
  
   open($f ,"<",$infilecsv) or die print "can't open '$f' $!\n";
   open($o ,">>",$outfilecsv) or die print "can't open '$o' $!\n";
   
   while (my $line = <$f>){
      chomp $line;
	  #print $line."\n";
	  my @fields = split "," , $line;
	  #print $fields[0]."\n";
	  my $claim = $fields[0];
	  $staticSql=~s/\?/$claim/;
	  #print $sql."\n";
      $sth = &exec_query($staticSql) or return;
	  my $ref;
		$ref = $sth->fetchall_arrayref;
		print "Number of rows returned is ", 0 + @{$ref}, "\n";
			foreach $r (@{$ref})
			{
			print $o join("\t", @{$r}), "\n";
		}
			#print $o "\n" unless $#row<1;
		$staticSql=$sql;
   }

     close $f,$o;
	 $sth->finish();

sub printhelp{
		print "PARAMETERS:\n\t<DSN name> <inputcsvfile> <outputfile> <sqlStatemnt>\n\tTo pass the first field from <inputcsvfile> use '?' in sql string\n\n";
		exit;
}

	 
sub connect_db{
	#my $in = shift;
    	my ($db, $username, $password,$data_source);
    	$db='classifieds';
    	$data_source ='dbi:ODBC:'.$dsn;
    	$username = '';
    	$password = '';
    	
	# connects to MSSQL.
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
     #exit;
    return $sth;
}