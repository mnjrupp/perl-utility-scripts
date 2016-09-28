#!perl -w
use strict;
#use warnings;
use DBI;
use DBD::ODBC;


our $DBH = undef;

my $sth = undef;
my($o,$s,$staticSql,$r,$sql,$col_name,$headersql);
my $dirpath="PATH WHERE YOU WANT TO WRITE THE FILES";

# Array of sql files
my @sqlf = ("Zip Exclusions.sql",
			"State Exclusions.sql",
			"ClaimsAlreadyWorked.sql",
			"PR06 No Match.sql",
			"Trading Partner Exclusions.sql"

			);
# Array of names of the outputs
# Should equal the # of sql files
my @outfilecsv = ("zipExcl",
				"STExcl",
				"ClaimsAlreadyWorked",
				"pr06NoMatch",
				"tradingpartnerExcl"

				);

		my ($sec,$min,$hour,$mday,$mon,$year,$wday,$yday,$isdst) = localtime(time);
		# Clean up the datetime segments
		$year+=1900;
		$mon = substr("0".($mon+1),-2);
		$mday = substr("0".$mday,-2);
		
	my $count = 0;	
foreach my $sq (@sqlf){
	if (not defined $sq or !-e $sq) {print "can't open $!\n";}

	# Need to read in the sql file.
	# the Input Record Seperator can be changed 
	# using the $/: but it has to be localized 
	# because it is global and the change would effect
	# reading of the other two files

	 open($s,"<",$sq);
	 {
	 local $/ = undef;
	 $sql = <$s>;
	 close $s;
	 }
	   
	  #Remove Carraige Returns and New Line Feeds
	  $sql=~s/\n/ /g;
	  
	  
	  #print $header."\n";exit;
	 $staticSql=$sql;
	 $headersql=$sql;
	 $headersql=~s/SELECT/SELECT TOP(1)/i;	
     #print $headersql,"\n";
	 $DBH = &connect_db or return ;

       my $outf = $dirpath.$outfilecsv[$count]."_".$mon.$mday.$year.$min.$sec.".csv";
	  #delete file if exists
	  if(-e $outf){unlink $outf;}
	  
	   # open($f ,"<",$infilecsv) or die print "can't open $infilecsv $!\n";
	   open($o ,">>",$outf) or die print "can't open $outf $!\n";
	   
		 # Retrieve the columns from the sth->{NAME}
		  $sth = &exec_query($headersql) or return;
		  
		  
		   for (my $i = 0; $i < $sth->{NUM_OF_FIELDS}; $i++) {
				$col_name = qq~$sth->{NAME}->[$i]\t~;
				print $o $col_name;
			}
			
			print $o "\n";
			
			# requery and pull data
			$sth = &exec_query($staticSql) or return;
		  my $ref;
			$ref = $sth->fetchall_arrayref;
			#print "Number of rows returned is ", 0 + @{$ref}, "\n";
				foreach $r (@{$ref})
				{
			
				 my $str = join("\t", @{$r});
					
					$str=~s/(\r|\n)+/ /g;
					#$str=~s/\s{6,}/ /g;
				print $o $str, "\n";
			}
				#print $o "\n" unless $#row<1;
			#$staticSql=$sql;
	   #}

		 close $o;
		 $sth->finish();
         $count++;
	 }
	 
	 
sub printhelp{
		print "PARAMETERS:\n\t<inputcsvfile> <outputfile> <sqlFile>\n\tTo pass the first field from <inputcsvfile> use '?' in sql string\n\n";
		exit;
}

	 
sub connect_db{
	#my $in = shift;
    	my ($db, $username, $password,$data_source);
    	$db='classifieds';
    	$data_source ='dbi:ODBC:NAME OF DSN';
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
    $sth->execute() or print "Error running the query :". $sth ->errstr()."\n<P>Query: $query"; 
     #exit;
    return $sth;
}