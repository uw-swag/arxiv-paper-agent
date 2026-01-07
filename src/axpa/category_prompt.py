from enum import Enum

class ArxivCategory(Enum):

    CS_AI = {
        "code": "cs.AI",
        "category": "Artificial Intelligence",
        "description":
            "Covers all areas of AI except Vision, Robotics, Machine Learning, Multiagent Systems, and Computation and Language (Natural Language Processing), which have separate subject areas. In particular, includes Expert Systems, Theorem Proving (although this may overlap with Logic in Computer Science), Knowledge Representation, Planning, and Uncertainty in AI."
    }

    CS_AR = {
        "code": "cs.AR",
        "category": "Hardware Architecture",
        "description":
            "Covers systems organization and hardware architecture."
    }

    CS_CC = {
        "code": "cs.CC",
        "category": "Computational Complexity",
        "description":
            "Covers models of computation, complexity classes, structural complexity, complexity tradeoffs, upper and lower bounds."
    }

    



"""

* cs.CE - Computational Engineering, Finance, and Science
Covers applications of computer science to the mathematical modeling of complex systems in the fields of science, engineering, and finance. Papers here are interdisciplinary and applications-oriented, focusing on techniques and tools that enable challenging computational simulations to be performed, for which the use of supercomputers or distributed computing platforms is often required.

* cs.CL - Computation and Language
Covers natural language processing.

* cs.CR - Cryptography and Security
Covers all areas of cryptography and security including authentication, public key cryptosytems, proof-carrying code, etc. 

* cs.CV - Computer Vision and Pattern Recognition
Covers image processing, computer vision, pattern recognition, and scene understanding.

* cs.CY - Computers and Society
Covers impact of computers on society, computer ethics, information technology and public policy, legal aspects of computing, computers and education.

* cs.DB - Databases
Covers database management, datamining, and data processing.

* cs.DC - Distributed, Parallel, and Cluster Computing
Covers fault-tolerance, distributed algorithms, stabilility, parallel computation, and cluster computing.

* cs.DL - Digital Libraries
Covers all aspects of the digital library design and document and text creation. Note that there will be some overlap with Information Retrieval (which is a separate subject area).

* cs.DM - Discrete Mathematics
Covers combinatorics, graph theory, applications of probability. 

* cs.DS - Data Structures and Algorithms
Covers data structures and analysis of algorithms.
    
* cs.ET - Emerging Technologies
Covers approaches to information processing (computing, communication, sensing) and bio-chemical analysis based on alternatives to silicon CMOS-based technologies, such as nanoscale electronic, photonic, spin-based, superconducting, mechanical, bio-chemical and quantum technologies (this list is not exclusive).

* cs.FL - Formal Languages and Automata Theory
Covers automata theory, formal language theory, grammars, and combinatorics on words.

* cs.GL - General Literature
Covers introductory material, survey material, predictions of future trends, biographies, and miscellaneous computer-science related material.

* cs.GR - Graphics
Covers all aspects of computer graphics.

* cs.GT - Computer Science and Game Theory
Covers all theoretical and applied aspects at the intersection of computer science and game theory, including work in mechanism design, learning in games (which may overlap with Learning), foundations of agent modeling in games (which may overlap with Multiagent systems), coordination, specification and formal methods for non-cooperative computational environments. The area also deals with applications of game theory to areas such as electronic commerce.

* cs.HC - Human-Computer Interaction
Covers human factors, user interfaces, and collaborative computing.

* cs.IR - Information Retrieval
Covers indexing, dictionaries, retrieval, content and analysis.

* cs.IT - Information Theory
Covers theoretical and experimental aspects of information theory and coding.

* cs.LG - Machine Learning
Papers on all aspects of machine learning research (supervised, unsupervised, reinforcement learning, bandit problems, and so on) including also robustness, explanation, fairness, and methodology. cs.LG is also an appropriate primary category for applications of machine learning methods.

* cs.LO - Logic in Computer Science
Covers all aspects of logic in computer science, including finite model theory, logics of programs, modal logic, and program verification. Programming language semantics should have Programming Languages as the primary subject area.

* cs.MA - Multiagent Systems
Covers multiagent systems, distributed artificial intelligence, intelligent agents, coordinated interactions. and practical applications.

* cs.MM - Multimedia
Covers all aspects of multimedia computing, including multimedia data representation, processing, analysis, and applications.

* cs.MS - Mathematical Software
Covers all aspects of mathematical software, including algorithms, design, implementation, testing, and applications.

* cs.NA - Numerical Analysis
cs.NA is an alias for math.NA.

* cs.NE - Neural and Evolutionary Computing
Covers neural networks, connectionism, genetic algorithms, artificial life, adaptive behavior.

* cs.NI - Networking and Internet Architecture
Covers all aspects of computer communication networks, including network architecture and design, network protocols, and internetwork standards (like TCP/IP). Also includes topics, such as web caching, that are directly relevant to Internet architecture and performance.

* cs.OH - Other Computer Science
This is the classification to use for documents that do not fit anywhere else.

* cs.OS - Operating Systems
Covers operating systems, file systems, system administration, etc.

* cs.PF - Performance
Covers performance measurement and evaluation, queueing, and simulation.

* cs.PL - Programming Languages
Covers programming language semantics, language features, programming approaches (such as object-oriented programming, functional programming, logic programming). Also includes material on compilers oriented towards programming languages; other material on compilers may be more appropriate in Architecture (AR).

* cs.RO - Robotics
Covers all aspects of robotics. 

* cs.SC - Symbolic Computation
Covers computer algebra, symbolic and algebraic computation, and automated theorem proving.

* cs.SD - Sound
Covers all aspects of computing with sound, and sound as an information channel. Includes models of sound, analysis and synthesis, audio user interfaces, sonification of data, computer music, and sound signal processing.

* cs.SE - Software Engineering
Covers design tools, software metrics, testing and debugging, programming environments, etc. Roughly includes material in all of ACM Subject Classes D.2, except that D.2.4 (program verification) should probably have Logics in Computer Science as the primary subject area.

* cs.SI - Social and Information Networks
Covers the design, analysis, and modeling of social and information networks, including their applications for on-line information access, communication, and interaction, and their roles as datasets in the exploration of questions in these and other domains, including connections to the social and biological sciences. Papers on computer communication systems and network protocols (e.g. TCP/IP) are generally a closer fit to the Networking and Internet Architecture (cs.NI) category.

* cs.SY - Systems and Control
cs.SY is an alias for eess.SY. This section includes theoretical and experimental research covering all facets of automatic control systems. The section is focused on methods of control system analysis and design using tools of modeling, simulation and optimization.
"""