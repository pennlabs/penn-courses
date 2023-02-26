const course1 = {
    "dept": "CIS",
    "number": 110,
    "title": "Introduction to Computer Programming (with Java, for Beginners",
    "description": "Introduction to Computer Programming is the first course in our series introducing students to computer science. In this class you will learn the fundamentals of computer programming in Java, with emphasis on applications in science and engineering. You will also learn about the broader field of computer science and algorithmic thinking, the fundamental approach that computer scientists take to solving problems."
  }
const course2 = 
  {
    "dept": "CIS",
    "number": 120,
    "title": "Programming Languages and Techniques I",
    "description": "A fast-paced introduction to the fundamental concepts of programming and software design.  This course assumes some previous programming experience, at the level of a high school computer science class or CIS110.  (If you got at least 4 in the AP Computer Science A or AB exam, you will do great.)  No specific programming language background is assumed: basic experience with any language (for instance Java, C, C++, VB, Python, Perl, or Scheme) is fine.  If you have never programmed before, you should take CIS 110 first."
  }
const course3 = 
  {
    "dept": "CIS",
    "number": 121,
    "title": "Programming Languages and Techniques I",
    "prereqs": ["CIS 120", "CIS 160"],
    "description": "This is a course about Algorithms and Data Structures using the JAVA programming language. We introduce the basic concepts about complexity of an algorithm and methods on how to compute the running time of algorithms. Then, we describe data structures like stacks, queues, maps, trees, and graphs, and we construct efficient algorithms based on these representations. The course builds upon existing implementations of basic data structures in JAVA and extends them for the structures like trees, studying the performance of operations on such structures, and their efficiency when used in real-world applications. A large project introducing students to the challenges of software engineering concludes the course."
  }
const course4 = 
  {
    "dept": "CIS",
    "number": 160,
    "title": "Mathematical Foundations of Computer Scienc",
    "description": "What are the basic mathematical concepts and techniques needed in computer science? This course provides an introduction to proof principles and logics, functions and relations, induction principles, combinatorics and graph theory, as well as a rigorous grounding in writing and reading mathematical proofs."
  }

const course5 = {
  "dept": "CIS",
  "number": 241,
  "title": "Introduction to Computer Architectur",
  "prereqs": ["CIS 110 or equivalent experience"],
  "description": "You know how to program, but do you know how computers really work? How do millions of transistors come together to form a complete computing system? This bottom-up course begins with transistors and simple computer hardware structures, continues with low-level programming using primitive machine instructions, and finishes with an introduction to the C programming language. This course is a broad introduction to all aspects of computer systems architecture and serves as the foundation for subsequent computer systems courses, such as Digital Systems Organization and Design (CIS 371), Computer Operating Systems (CIS 380), and Compilers and Interpreters (CIS 341)."
}

export const coursesSpring2023 = [
  {
      "dept": "CIS",
      "number": 240,
      "title": "Introduction to Computer Architectur",
      "prereqs": ["CIS 110 or equivalent experience"],
      "description": "You know how to program, but do you know how computers really work? How do millions of transistors come together to form a complete computing system? This bottom-up course begins with transistors and simple computer hardware structures, continues with low-level programming using primitive machine instructions, and finishes with an introduction to the C programming language. This course is a broad introduction to all aspects of computer systems architecture and serves as the foundation for subsequent computer systems courses, such as Digital Systems Organization and Design (CIS 371), Computer Operating Systems (CIS 380), and Compilers and Interpreters (CIS 341)."
    },
    {
      "dept": "CIS",
      "number": 261,
      "title": "Discrete Probability, Stochastic Processes, and Statistical Inference",
      "prereqs": ["CIS 160"],
      "description": "The purpose of this course is to provide a 1 CU educational experience which tightly integrates the theory and applications of discrete probability, discrete stochastic processes, and discrete statistical inference in the study of computer science.\nThe intended audience for this class is both those students who are CS majors as well as those intending to be CS majors. Specifically, it will be assumed that the students will know: Set Theory, Mathematical Induction, Number Theory, Functions, Equivalence Relations, Partial-Order Relations, Combinatorics, and Graph Theory at the level currently covered in CIS 160. This course could be taken immediately following CIS 160. Computation and Programming will play an essential role in this course. The students will be expected to use the Maple programming environment in homework exercises which will include: numerical and symbolic computations, simulations, and graphical displays."
    },
    {
      "dept": "CIS",
      "number": 262,
      "title": "Automata, Computability, and Complexity",
      "prereqs": ["CIS 160"],
      "description": "This course explores questions fundamental to computer science such as which problems cannot be solved by computers, can we formalize computing as a mathematical concept without relying upon the specifics of programming languages and computing platforms, and which problems can be solved efficiently. The topics include finite automata and regular languages, context-free grammars and pushdown automata, Turing machines and undecidability, tractability and NP-completeness. The course emphasizes rigorous mathematical reasoning as well as connections to practical computing problems such as text processing, parsing, XML query languages, and program verification."
    },
    {
      "dept": "CIS",
      "number": 320,
      "title": "Introduction to Algorithms",
      "prereqs": ["CIS 120", "CIS 121", "CIS 160", "CIS 262"],
      "description": "How do you optimally encode a text file? How do you find shortest paths in a map? How do you design a communication network? How do you route data in a network? What are the limits of efficient computation? This course gives a comprehensive introduction to design and analysis of algorithms, and answers along the way to these and many other interesting computational questions. You will learn about problem-solving; advanced data structures such as universal hashing and red-black trees; advanced design and analysis techniques such as dynamic programming and amortized analysis; graph algorithms such as minimum spanning trees and network flows; NP-completeness theory; and approximation algorithms."
    },
  
    {
      "dept": "CIS",
      "number": 331,
      "title": "Intro to Networks and Security",
      "prereqs": ["CIS 160", "CIS 240"],
  
      "description": "This course introduces principles and practices of computer and network security. We will cover basic concepts, threat models, and the security mindset; an introduction to cryptography and cryptographic protocols including encryption, authentication, message authentication codes, hash functions, public-key cryptography, and secure channels; an introduction to networks and network security including IP, TCP, routing, network protocols, web architecture, attacks, firewalls, and intrusion detection systems; an introduction to software security including defensive programming, memory protection, buffer overflows, and malware; and discuss broader issues and case studies such as privacy, security and the law, digital rights management, denial of service, and ethics."
    }
]

export const coursesFall2023 = [
  {
    "dept": "CIS",
    "number": 334,
    "title": "Advanced Topics in Algorithms",
    "prereqs": ["CIS 320"],
    "description": "Can you check if two large documents are identical by examining a small number of bits? Can you verify that a program has correctly computed a function without ever computing the function? Can students compute the average score on an exam without ever revealing their scores to each other? Can you be convinced of the correctness of an assertion without ever seeing the proof? The answer to all these questions is in the affirmative provided we allow the use of randomization. Over the past few decades, randomization has emerged as a powerful resource in algorithm design. This course would focus on powerful general techniques for designing randomized algorithms as well as specific representative applications in various domains, including approximation algorithms,  cryptography and number theory, data structure design, online algorithms, and parallel and distributed computation."
  },
  {
    "dept": "CIS",
    "number": 341,
    "title": "Compilers and Interpreters",
    "prereqs": ["CIS 121", "CIS 240"],
    "description": "You know how to program, but do you know how to implement a programming language? In CIS341 you'll learn how to build a compiler. Topics covered include: lexical analysis, grammars and parsing, intermediate representations, syntax-directed translation, code generation, type checking, simple dataflow and control-flow analyses, and optimizations. Along the way, we study objects and inheritance, first-class functions (closures), data representation and runtime-support issues such as garbage collection. This is a challenging, implementation-oriented course in which students build a full compiler from a simple, typed object-oriented language to fully operational x86 assembly. The course projects are implemented using OCaml, but no knowledge of OCaml is assumed."
  },
  {
    "dept": "CIS",
    "number": 371,
    "title": "Computer Organization and Design",
    "prereqs": ["CIS 240"],
    "description": "This is the second computer organization course and focuses on computer hardware design. Topics covered are: (1) basic digital system design including finite state machines, (2) instruction set design and simple RISC assembly programming, (3) quantitative evaluation of computer performance, (4) circuits for integer and floating-point arithmetic, (5) datapath and control, (6) micro-programming, (7) pipelining, (8) storage hierarchy and virtual memory, (9) input/output, (10) different forms of parallelism including instruction level parallelism, data-level parallelism using both vectors and message-passing multi-processors, and thread-level parallelism using shared memory multiprocessors. Basic cache coherence and synchronization."
  },

  {
    "dept": "CIS",
    "number": 380,
    "title": "Computer Operating Systems",
    "prereqs": ["CIS 240"],
    "description": "This course surveys methods and algorithms used in modern operating systems. Concurrent distributed operation is emphasized. The main topics covered are as follows: process synchronization; interprocess communications; concurrent/distributed programming languages; resource allocation and deadlock; virtual memory; protection and security; distributed operation; distributed data; performance evaluation."
  }
]

export const coursesSpring2024 = [
  {
    "dept": "CIS",
    "number": 390,
    "title": "Robotics: Planning and Perception",
    "prereqs": ["CIS 121", "MATH 240 or equivalent"],
    "description": "This introductory course will present basic principles of robotics with an emphasis  to computer science aspects. Algorithms for planning and perception will be studied and implemented on actual robots. While planning is a fundamental problem in artificial intelligence and decision making, robot planning refers to finding a path from A to B in the presence of obstacles and by complying with the kinematic constraints of the robot. Perception involves the estimation of the robot’s motion and path as well as the shape of the environment from sensors. In this course, algorithms will be implemented in Python on mobile platforms on ground and in the air. No prior experience with Python is needed but we require knowledge of data structures, linear algebra, and basic probability."
  },

  {
    "dept": "CIS",
    "number": 398,
    "title": "Quantum Computer and Information Science",
    "prereqs": ["PHYS 151", "MATH 240", "MATH 312/314", "CIS 160", "CIS 262"],
    "description": "The purpose of this course is to introduce undergraduate students in computer science and engineering to quantum computers (QC) and quantum information science (QIS). This course is meant primarily for juniors and seniors in CIS. No prior knowledge of quantum mechanics (QM) is assumed."
  },

  {
    "dept": "CIS",
    "number": 400,
    "title": "Senior Project",
    "prereqs": ["Senior standing or permission of instructor"],

    "description": "Design and implementation of a significant piece of work: software, hardware or theory. In addition, emphasis on technical writing and oral communication skills. Students must have an abstract of their Senior Project, which is approved and signed by a Project Adviser, at the end of the second week of Fall classes. The project continues during two semesters; students must enroll in CIS 401 during the second semester. At the end of the first semester, students are required to submit an intermediate report and give a class presentation describing their project and progress. Grades are based on technical writing skills (as per submitted report), oral presentation skills (as per class presentation) and progress on the project. These are evaluated by the Project Adviser and the Course Instructor."
  },

  {
    "dept": "CIS",
    "number": 401,
    "title": "Senior Project",
    "prereqs": ["CIS 400", "Senior standing or permission of instructor"],

    "description": "Continuation of CIS 400. Design and implementation of a significant piece of work: software, hardware or theory. Students are required to submit a final written report and give a final presentation and demonstration of their project. Grades are based on the report, the presentation and the satisfactory completion of the project. These are evaluated by the Project Advisor and the Course Instructor."
  },
  {
    "dept": "CIS",
    "number": 402,
    "title": "Senior Project",
    "prereqs": ["CIS 400", "Senior standing or permission of instructor"],

    "description": "Continuation of CIS 400. Design and implementation of a significant piece of work: software, hardware or theory. Students are required to submit a final written report and give a final presentation and demonstration of their project. Grades are based on the report, the presentation and the satisfactory completion of the project. These are evaluated by the Project Advisor and the Course Instructor."
  }
]


export default [course1, course2, course3, course4, course5];