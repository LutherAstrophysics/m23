from m23.exceptions.basics import ArgsLengthMisMatch

### noOfArgs
###
### meant to be used as a decorator that takes in
###   the number of args to be passed to the function 
###   being decorated
###
### raises ArgsLengthMisMatch error otherwise
###
def noOfArgs(noOfArgs):
    def inn(myFunc):
        def inner(*args, **kwargs):
            if noOfArgs == len(args):
                myFunc(*args, **kwargs)
            else:
                print(f"M23 ERROR, mismatchNoOfArgs in "\
                        +f"{myFunc} required {noOfArgs}, given {len(args)}")
                raise ArgsLengthMisMatch
        return inner
    return inn
