from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


@dataclass(frozen=True)
class ArxivCategoryInfo:
    code: str
    name: str
    description: str


class ArxivCategory(Enum):
    CS_AI = ArxivCategoryInfo(
        code="cs.AI",
        name="Artificial Intelligence",
        description=(
            "Covers all areas of AI except Vision, Robotics, Machine Learning, "
            "Multiagent Systems, and Computation and Language (Natural Language Processing), "
            "which have separate subject areas. In particular, includes Expert Systems, "
            "Theorem Proving (although this may overlap with Logic in Computer Science), "
            "Knowledge Representation, Planning, and Uncertainty in AI."
        ),
    )

    CS_AR = ArxivCategoryInfo(
        code="cs.AR",
        name="Hardware Architecture",
        description="Covers systems organization and hardware architecture.",
    )

    CS_CC = ArxivCategoryInfo(
        code="cs.CC",
        name="Computational Complexity",
        description=(
            "Covers models of computation, complexity classes, structural complexity, "
            "complexity tradeoffs, upper and lower bounds."
        ),
    )

    CS_CE = ArxivCategoryInfo(
        code="cs.CE",
        name="Computational Engineering, Finance, and Science",
        description=(
            "Covers applications of computer science to the mathematical modeling of complex systems "
            "in the fields of science, engineering, and finance. Papers here are interdisciplinary "
            "and applications-oriented, focusing on techniques and tools that enable challenging "
            "computational simulations to be performed, for which the use of supercomputers or "
            "distributed computing platforms is often required."
        ),
    )

    CS_CL = ArxivCategoryInfo(
        code="cs.CL",
        name="Computation and Language",
        description="Covers natural language processing.",
    )

    CS_CR = ArxivCategoryInfo(
        code="cs.CR",
        name="Cryptography and Security",
        description=(
            "Covers all areas of cryptography and security including authentication, "
            "public key cryptosystems, proof-carrying code, etc."
        ),
    )

    CS_CV = ArxivCategoryInfo(
        code="cs.CV",
        name="Computer Vision and Pattern Recognition",
        description="Covers image processing, computer vision, pattern recognition, and scene understanding.",
    )

    CS_CY = ArxivCategoryInfo(
        code="cs.CY",
        name="Computers and Society",
        description=(
            "Covers impact of computers on society, computer ethics, information technology and "
            "public policy, legal aspects of computing, computers and education."
        ),
    )

    CS_DB = ArxivCategoryInfo(
        code="cs.DB",
        name="Databases",
        description="Covers database management, datamining, and data processing.",
    )

    CS_DC = ArxivCategoryInfo(
        code="cs.DC",
        name="Distributed, Parallel, and Cluster Computing",
        description=(
            "Covers fault-tolerance, distributed algorithms, stability, parallel computation, "
            "and cluster computing."
        ),
    )

    CS_DL = ArxivCategoryInfo(
        code="cs.DL",
        name="Digital Libraries",
        description=(
            "Covers all aspects of the digital library design and document and text creation. "
            "Note that there will be some overlap with Information Retrieval (separate subject area)."
        ),
    )

    CS_DM = ArxivCategoryInfo(
        code="cs.DM",
        name="Discrete Mathematics",
        description="Covers combinatorics, graph theory, applications of probability.",
    )

    CS_DS = ArxivCategoryInfo(
        code="cs.DS",
        name="Data Structures and Algorithms",
        description="Covers data structures and analysis of algorithms.",
    )

    CS_ET = ArxivCategoryInfo(
        code="cs.ET",
        name="Emerging Technologies",
        description=(
            "Covers approaches to information processing and bio-chemical analysis based on "
            "alternatives to silicon CMOS-based technologies."
        ),
    )

    CS_FL = ArxivCategoryInfo(
        code="cs.FL",
        name="Formal Languages and Automata Theory",
        description="Covers automata theory, formal language theory, grammars, and combinatorics on words.",
    )

    CS_GL = ArxivCategoryInfo(
        code="cs.GL",
        name="General Literature",
        description=(
            "Covers introductory material, survey material, predictions of future trends, biographies, "
            "and miscellaneous computer-science related material."
        ),
    )

    CS_GR = ArxivCategoryInfo(
        code="cs.GR",
        name="Graphics",
        description="Covers all aspects of computer graphics.",
    )

    CS_GT = ArxivCategoryInfo(
        code="cs.GT",
        name="Computer Science and Game Theory",
        description=(
            "Covers theoretical and applied aspects at the intersection of computer science and game theory, "
            "including mechanism design, learning in games, agent modeling, coordination, and applications "
            "to electronic commerce."
        ),
    )

    CS_HC = ArxivCategoryInfo(
        code="cs.HC",
        name="Human-Computer Interaction",
        description="Covers human factors, user interfaces, and collaborative computing.",
    )

    CS_IR = ArxivCategoryInfo(
        code="cs.IR",
        name="Information Retrieval",
        description="Covers indexing, dictionaries, retrieval, content and analysis.",
    )

    CS_IT = ArxivCategoryInfo(
        code="cs.IT",
        name="Information Theory",
        description="Covers theoretical and experimental aspects of information theory and coding.",
    )

    CS_LG = ArxivCategoryInfo(
        code="cs.LG",
        name="Machine Learning",
        description=(
            "Papers on all aspects of machine learning research including robustness, explanation, fairness, "
            "and methodology. cs.LG is also appropriate for applications of machine learning methods."
        ),
    )

    CS_LO = ArxivCategoryInfo(
        code="cs.LO",
        name="Logic in Computer Science",
        description=(
            "Covers all aspects of logic in computer science, including finite model theory, logics of programs, "
            "modal logic, and program verification."
        ),
    )

    CS_MA = ArxivCategoryInfo(
        code="cs.MA",
        name="Multiagent Systems",
        description="Covers multiagent systems, distributed AI, intelligent agents, coordinated interactions.",
    )

    CS_MM = ArxivCategoryInfo(
        code="cs.MM",
        name="Multimedia",
        description="Covers all aspects of multimedia computing.",
    )

    CS_MS = ArxivCategoryInfo(
        code="cs.MS",
        name="Mathematical Software",
        description="Covers all aspects of mathematical software, including algorithms, design, implementation, testing.",
    )

    CS_NA = ArxivCategoryInfo(
        code="cs.NA",
        name="Numerical Analysis",
        description="cs.NA is an alias for math.NA.",
    )

    CS_NE = ArxivCategoryInfo(
        code="cs.NE",
        name="Neural and Evolutionary Computing",
        description="Covers neural networks, connectionism, genetic algorithms, artificial life, adaptive behavior.",
    )

    CS_NI = ArxivCategoryInfo(
        code="cs.NI",
        name="Networking and Internet Architecture",
        description=(
            "Covers all aspects of computer communication networks, including network architecture and design, "
            "network protocols, and internetwork standards."
        ),
    )

    CS_OS = ArxivCategoryInfo(
        code="cs.OS",
        name="Operating Systems",
        description="Covers operating systems, file systems, system administration, etc.",
    )

    CS_PF = ArxivCategoryInfo(
        code="cs.PF",
        name="Performance",
        description="Covers performance measurement and evaluation, queueing, and simulation.",
    )

    CS_PL = ArxivCategoryInfo(
        code="cs.PL",
        name="Programming Languages",
        description=(
            "Covers programming language semantics, language features, programming approaches, and compilers "
            "oriented towards programming languages."
        ),
    )

    CS_RO = ArxivCategoryInfo(
        code="cs.RO",
        name="Robotics",
        description="Covers all aspects of robotics.",
    )

    CS_SC = ArxivCategoryInfo(
        code="cs.SC",
        name="Symbolic Computation",
        description="Covers computer algebra, symbolic and algebraic computation, and automated theorem proving.",
    )

    CS_SD = ArxivCategoryInfo(
        code="cs.SD",
        name="Sound",
        description="Covers all aspects of computing with sound, audio analysis/synthesis, and sound signal processing.",
    )

    CS_SE = ArxivCategoryInfo(
        code="cs.SE",
        name="Software Engineering",
        description="Covers design tools, software metrics, testing and debugging, programming environments, etc.",
    )

    CS_SI = ArxivCategoryInfo(
        code="cs.SI",
        name="Social and Information Networks",
        description=(
            "Covers design, analysis, and modeling of social and information networks and their applications."
        ),
    )

    CS_SY = ArxivCategoryInfo(
        code="cs.SY",
        name="Systems and Control",
        description=(
            "cs.SY is an alias for eess.SY. Includes methods of control system analysis and design using "
            "modeling, simulation and optimization."
        ),
    )


def all_category_codes() -> list[str]:
    return [c.value.code for c in ArxivCategory]

def validate_category_codes(codes: Iterable[str]) -> tuple[list[str], list[str]]:
    allowed = set(all_category_codes())
    ok: list[str] = []
    bad: list[str] = []
    for code in codes:
        if code in allowed:
            ok.append(code)
        else:
            bad.append(code)
    return ok, bad