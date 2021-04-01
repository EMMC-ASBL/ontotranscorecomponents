This toolchain is made of a script which automates the EMMO ontology import process done by the wrapper, which is the second component, written by Daniele Toti: a Fact++ standalone reasoner, which includes the URI-remapping functionality (version 1.2.0).

## Requirements
The developed script is written as a bash script, requiring a Linux-like OS; you've to grant it execution privileges.
Make sure you have a Java Virtual Machine (JRE or JDK) version 1.8 installed in your system, it's needed for the wrapper.

## How to use this toolchain
Firstly make sure that EMMO to Stardog script `e2s.sh` is in the same folder of the wrapper, then you can run it by simply calling it without parameters: it will fetch the ontology master release.
It's possible to specify `-o` to specify a path for the onotlogy to collect (local or online) or `-d` to choose a name for the Stardog database (useful when importing more times, indeed this script will note erase any database already in Stardog - databases should have unique names).

### Wrapper setup
Make sure that in `properties/reasoner.properties` the OS-dependent library for the Fact++ reasoner is correctly specified for the `factpp.jni.path` property, namely one of the following:

- `factpp.jni.path=jnilibs/64bit/FaCTPlusPlusJNI.dll` – _for Windows 64 bit_
- `factpp.jni.path=jnilibs/64bit/libFaCTPlusPlusJNI.jnilib` – _for Mac 64 bit (not tested)_
- `factpp.jni.path=jnilibs/64bit/libFaCTPlusPlusJNI.so` – _for Linux 64 bit_

The 32 bit versions are available in the jnilibs directory as well. The default property you will see in the file (the only one not commented) is for Windows 64 bit.

Then, you can easily run it with the default options by using the included .bat or .sh file. By default, it connects to EMMO’s 1.0.0-alpha2 remote URL and produces its inferred version in rdf/xml format with its URIs remapped, and saves it to “emmo-inferred.rdf” within the directory of the tool.

### The wrapper

*These options are only valid without the script!*

The standalone wrapper can run directly by calling the factplusplus.jar via
```
java -jar factplusplus.jar
```
and specify a number of parameters with the following syntax
```
-s <source_ontology>
-d <destination_filepath>
-o <options>
-f <output_format>
-r <Boolean_flag_for_generating_the_inferred_ontology_or_not>
-m <Boolean_flag_for_remapping_URIs_or_not>
```
regardless of the input order of the pairs, where:
-	`<source_ontology>` can be a URI or a filepath for the entry file of the ontology with all of the imports (default=”https://emmo.info/emmo/1.0.0-alpha2”)
-	`<destination_filepath>` is the full filepath of the file to be generated (default=emmo-inferred.rdf in the root directory of the tool)
-	`<options>` for customizing the axioms to be inferred, (i.e. secpodj), which mean:
-	`<output_format>` can be either rdf, ttl or owl, but with EMMO at the moment I would recommend leaving the default value (rdf)
-	`<Boolean_flag_for_generating_the_inferred_ontology_or_not>` True or False (self-explicative)
-	`<Boolean_flag_for_remapping_URIs_or_not>` True or False (self-explicative)

-	`s` subclasses
-	`e` equivalent classes
-	`c` class assertions
-	`p` property assertions
-	`o` object property characteristics
-	`d` datatype property characteristics
-	`j` disjoint classes
(default: nothing specified, it uses the default Fact++ reasoning mechanism)