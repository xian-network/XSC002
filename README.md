# XST002 // Permit

- An adaptation of [EIP-2612](https://eips.ethereum.org/EIPS/eip-2612) for Xian.
- Allows for a user to grant a spender a certain amount of tokens to spend on their behalf, without having to submit a transaction to the network.

### How it works :

The user constructs a message to sign, and the contract verifies the signature.

- The message follows consists of the following fields:
  - `owner`: The address of the owner of the permit
  - `spender`: The address of the spender
  - `value`: The amount of tokens to spend
  - `deadline`: The deadline for the permit
  - `signature`: The signature of the message
  - `contract`: The name of the contract to which the permit is granted

- The user / frontend dapp will construct the message like so : 
    - `msg = f"{owner}:{spender}:{value}:{deadline}:{contract}" `
    - `signature = wallet.sign_msg(msg)`

- The frontend dapp will then call `permit(owner, spender, value, deadline, signature)` on the contract
-  `permit()` will :
    - construct the message like so : 
        - `msg = f"{owner}:{spender}:{value}:{deadline}:{ctx.this}"`
    - assert the deadline is greater than the current time.
    - create a `permit_hash` using SHA3 hash of `msg` and store it in `permits[permit_hash]`, to prevent replays.
    - assert `permit_hash` is in permits, if so, revert 
    - call `verify(msg, signature)`
    - if valid:
        - will add the `permit_hash` to `permits`
        - add the allowance to the spender