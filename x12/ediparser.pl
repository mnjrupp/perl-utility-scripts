#!perl -w
 use X12::Parser;

    # Create a parser object
    my $p = new X12::Parser;
    my($inputfile,$configfile)=@ARGV;
    # Parse a file with the transaction specific configuration file
    $p->parsefile ( 
        file => $inputfile,
        conf => $configfile
    );
	$p->print_tree;
	exit;

=head   while ( my ( $pos, $level, $loop ) = $p->get_next_pos_level_loop ) {
		#$pad = '  |' x $level;
		# print "       $pad--$loop\n";
		# $pad = '  |' x ( $level + 1 );
		# my @loop = $p->get_loop_segments;
		# foreach $segment (@loop) {
			# $index = sprintf( "%+7s", $pos++ );
			# print "$index$pad-- $segment\n";
		# }
		
		if($loop eq '2000'){
		 my @loop = $p->get_loop_segments;
		   foreach $segment (@loop) {
			 #$index = sprintf( "%+7s", $pos++ );
			 print "$segment\n";
		 }
		}
	}
=cut