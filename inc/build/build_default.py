from ebbs import Builder

#Class name is what is used at cli, so we defy convention here in favor of ease-of-use.
class default(Builder):
	def __init__(this, name="Default Builder"):
		super().__init__(name)

		this.supportedProjectTypes = []

	#Required Builder method. See that class for details.
	def DidBuildSucceed(this):
		return True #sure! why not?

	#Required Builder method. See that class for details.
	def Build(this):
		pass
