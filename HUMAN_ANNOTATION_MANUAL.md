# Human Annotation Manual

## Task Description
This guide pertains to the annotation of human-machine dialogues involving API calls. You will play the role of a user interacting with an assistant, responding to its inquiries. Where necessary, you should guide the assistant to invoke an API call, until it either successfully does so or exceeds the dialogue round limit (8 rounds). A total of 276 dialogue rounds need to be annotated.

At the start of each dialogue annotation session, the user has already issued an instruction to the system. However, this instruction is mostly incomplete, preventing the system from directly invoking an API call. Therefore, the system will ask follow-up questions to the user to gather the necessary information. In this role, you need to assist the system in completing the API call.

You must converse with the system based on the role of the context provided in the red box (pay particular attention to the Parameters section). When the system asks for information, you must strictly provide responses based on the values in the Parameters section. After inputting your response and pressing Enter, the system will reply based on your input. The dialogue may proceed over one or multiple rounds, with the desired outcome being the successful API call (indicated by the appearance of the green box in the image).

## Annotation Standards
Please adhere to the following guidelines:

1. Respond to the system using a brief and colloquial style. Keep sentences short and grammar simple.
2. When replying with information from the Parameters, use the exact wording from the Parameters. For example, if the Parameters say {"time": "1:00 PM"}, reply with "I'm departing at 1:00 PM," not "I'm departing at 13:00."
3. If the model asks for information not present in the Parameters, respond that you do not know.
4. If, after being provided with all the information from the Parameters, the model still does not invoke the function (a successful invocation would directly proceed to the next round) and instead instructs the user to conduct their own search (as shown in the image below), add a reply saying, "Can you just do xxx for me?" to prompt the model to execute the API. If there is still no progress to the next round, type "[fail]" in the input box to skip the current round.
